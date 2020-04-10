# -*- coding: utf-8 -*-

from colored import *
from random import *
import socket
import time
import sys
import remote_play


def play (map_title, team_1, team_1_type, team_2, team_2_type):



    """ Start the game and do the folowing function
    Parameter
    ----------
    map_tilte : name of the map file (str)
    team_1 : name of the team 1 (str)
    team_1_type : type of the team 1 (remote, human, AI) (str)
    team_2 : name of the team 2 (str)
    team_2_type : type of the team 2 (remote, human, AI) (str)

    
    Notes :
    --------
    The function start the game and do each phase with the function
    
    Versions
    --------
    specification : Pierre Merveille (v.1 24/02/20)
                    Kevin Schweitzer (v.2 27/03/20)

    Implémentation : Pierre Merveille (v.1 10/03/20)
                     Pierre Merveille (v.2 30/03/20)
    """

    #Prepare the variable for the game
    board, units_stats, max_upgrade, cost_upgrade, elements, color_team, ships, peaks, long, larg, teams = set_games(team_1,team_1_type , team_2,team_2_type, map_title)
    end_counter = 0
    team_id=(team_1,team_2)
    end = False
    link = False

    #Make a connection if there is one remote player
    if team_1_type == 'remote':
        connection = remote_play.create_connection(team_2, team_1, verbose=True)
        link=True
    if team_2_type == 'remote':
        connection = remote_play.create_connection(team_1, team_2, verbose=True)
        link=True

    #Start the game
    while end == False:
        order_list={}

        #Separate in 2 the round because there are 2 teams and start the connectique phase
        for team in teams :

            #Verify if the player is an human
            if teams[team]['player'] == 'human' :

                #Get the order from the human player
                order = input("Let's get %s's orders: "% teams[team]['team'])
                order_list[teams[team]['team']]= order

                #Give the order to the remote player if there is one
                if link :
                    remote_play.notify_remote_orders(connection, order)


            #Verify if the player is an remote player
            elif  teams[team]['player'] == 'remote':

                #Get the order from the remote player
                order_list[teams[team]['team']] = remote_play.get_remote_orders(connection)

            #Verify if the player is an AI
            elif teams[team]['player'] == 'AI':

                #Create the order from the AI
                order = create_order (long, larg, teams[team]['team'], ships, units_stats, peaks)
                order_list[teams[team]['team']] = order

                #Give the order to the remote player if there is one
                if link :
                    remote_play.notify_remote_orders(connection, order)
    
        #Separate in 2 the round because there are 2 teams and start the gameplay phase
        for team in color_team:

            #Get the team who is playing and the ennemy team
            if team==team_1:
                ennemy_team=team_2
            else :
                ennemy_team = team_1

            #get the order of the team wich play
            order = order_list[team]
            
            #Separate the instruction in category
            upgrade_list, create_list, move_list, attack_list, transfer_list = separate_instruction(order, ships, units_stats, board, team, peaks)

            #Create phase
            ships, board, units_stats = create_units(create_list, ships, team, board, units_stats,peaks)
            
            #Upgrade phase
            units_stats = upgrade(upgrade_list, team, units_stats, ships, max_upgrade, cost_upgrade)
            
            #Attack phase
            end_counter = attack(attack_list, board, units_stats, ships, team, ennemy_team, peaks, end_counter,color_team)
            
            #Move phase
            board, ships = move(move_list, ships, team, board, units_stats, peaks)
            
            #transfer phase
            ships, units_stats, peaks = transfer(transfer_list, ships, team, units_stats, peaks, board)
            
        #Do the update after the round
        units_stats = round_end(board, end_counter, units_stats, peaks, elements, color_team, ships)

        #Select the winner
        end, winner = end_game(color_team,units_stats,end_counter,team,ennemy_team)
    
    #Verify if there is a winner or if it's a draw
    if winner != 'NO':
        print ('%s is the winner.' % winner)
    else : 
        print ('The game ends in a draw.')

    #Close the connection if there was one
    if link : 
        remote_play.close_connection(connection)

def set_games (team_1, team_1_type, team_2, team_2_type, map_title) :
    """
    Create all the environnement of the game. Takes the data contained in the file and initializes the data structure (variable)

    Parametre :
    -----------
    map_tilte : name of the map file (str)
    team_1 : name of the team 1 (str)
    team_1_type : type of the team 1 (remote, human, AI) (str)
    team_2 : name of the team 2 (str)
    team_2_type : type of the team 2 (remote, human, AI) (str)

    Returns :
    ---------
    ships :  dictionnary with the statistics of each ship (tanker or cruiser)(dict)
    board : dictionnary with the coordinates of all boxes of the board which gives a list of element on this place (dict)
    units_states : states of each unit (dict)
    max_upgrade : dictionary containing the values for each upgrade (dict)
    cost_upgrade : dictionary containing the price for each upgrade (dict)
    peaks : dictionnary with informations about each peak (dict)
    long : length of the board (int)
    larg : width of the board (int)
    elements : dictionnary with the type of entity (cruiser, hub,...) with the charactere of each type (dict)
    
    Notes : 
    ------
    This function create the data structure like the representation of the board in data (dictionnary) and the states of the hub contains in the file, tuple of the upgrade, initialize
    the list of the ship (dictionnary) and the structures for the design containing the representation of the unit type (cruiser, tanker, peak, hub)

    
    Versions 
    --------
    specification : Pierre Merveille(v.1 23/02/20)
                    Anthony Pierard(v.2 28/02/20)
                    Johan Rochet(v.3 27/03/20)

    Implémentation : Merveille Pierre (v.1 10/03/20)
                     Johan Rochet (v.2 27/03/20)

    """
    
#Initialize the variable use for the design
    elements = {'hub' : '⚑' , 'cruiser': 'ѧ' , 'tanker' : 'ѫ' , 'peak' : 'ϟ'}
    color_team = {team_1 : fg(1), team_2: fg(4)}

    #Select the dimension of the map
    fh = open(map_title + ".eq",'r')
    lines= fh.readlines()
    board_dimension= lines[1][:-1].split(' ')
    long = int(board_dimension[0])
    larg = int(board_dimension[1])

    #Create the board
    for x in range (1, long + 1):
        for y in range ( 1, larg + 1):
            if x==1 and y==1:
                board = {(x,y) : {'list_entity' : ['   ']}}
            else:
                board[(x,y)] = {'list_entity': ['   ']}


    #Create the variable with the info of the cruiser, tanker and hub for each team and the common state
    units_stats  = {team_1 : { 'cruiser' : {'range' : 1 , 'move' : 10}, 'tanker': {'max_energy' : 600}, 'hub' :  {'coordinates' : 123, 'HP': 123, 'energy_point' :123, 'regeneration':123}},
                team_2 : { 'cruiser' : {'range' : 1 , 'move' : 10}, 'tanker': {'max_energy' : 600}, 'hub' :  {'coordinates' : 123, 'HP': 123, 'energy_point' :123, 'regeneration':123, }},
                'common' : {'cruiser' : {'max_energy' : 400, 'cost_attack' : 10, 'creation_cost' : 750, 'attack' : 1, 'max_HP': 100}, 'tanker' : {'creation_cost' : 1000, 'move': 0, 'max_HP': 50}, 'hub': {'max_energy_point' : 0}}}

    #Select the info of the hub in the file
    for ligne in range (3, 5):
        info_hub = lines[ligne][:-1].split(' ')    
        if ligne == 3 :
            name_team = team_1
        else:
            name_team = team_2
            
        board[(int(info_hub[0]), int(info_hub[1]))]['list_entity'] = [name_team]
        
        #put the hub stat in the variable units_stats
        units_stats[name_team]['hub']['coordinates'] = (int(info_hub[0]),int(info_hub[1]))
        units_stats[name_team]['hub']['HP'] = int(info_hub[2])
        units_stats[name_team]['hub']['energy_point'] =int(info_hub[3])
        units_stats[name_team]['hub']['regeneration'] = int(info_hub[4])
        units_stats['common']['hub']['max_energy_point'] = int(info_hub[3])


    #Select the info of the peaks in the file
    for index in range (6, len(lines)):

        info_peak = lines[index][:-1].split(' ')
        name_entity = 'peak' + str(index-5)
        
        #Create and place the stat peak in a dictionnary
        if index == 6:
            peaks = {name_entity : {'coordinates' : (int(info_peak[0]), int(info_peak[1])), 'storage' : int(info_peak[2])}}
        else:
            peaks[name_entity]= {'coordinates' : (int(info_peak[0]), int(info_peak[1])), 'storage' : int(info_peak[2])}

        #Put the peak on the board  
        board[(int(info_peak[0]), int(info_peak[1]))]['list_entity'] = [name_entity]

    
    #Get the stat for the upgrade
    max_upgrade = {'max_regen_upgrade' :  50,  'max_range_upgrade' : 5, 'max_travel_upgrade' : 5, 'max_capacity_upgrade' : 1200}
    cost_upgrade = {'cost_regen_upgrade' : 750, 'cost_range_upgrade' : 400, 'cost_travel_upgrade' : 500, 'cost_upgrade_capacity':600}

    
    ships ={}
    teams ={team_1 : team_1_type, team_2 : team_2_type}
    
    #ships ={'name' : {'coordinates' : , 'team' : , 'type' : , 'HP' : , 'energy_point': }

    #Display the board and the stat of the element (peak, cruiser,...)
    board_display(board, color_team, ships, peaks, units_stats, elements)
    display_stats(elements,color_team,ships,units_stats,peaks)

    return board, units_stats, max_upgrade, cost_upgrade, elements, color_team, ships, peaks, long,larg,teams
    
def end_game ( color_team, units_stats, end_counter, team, ennemy_team ): 

    """ Verify if game is finished 
    
    Parameters
    ----------
    color_team : dictionnary with the number of the team with the color of each team (dict)
    units_stats :dictionnary with the stats (different or common) of the teams (hub /ship) (dict)
    end_counter : number of rounds without attacks (float)
    team : name of the team which is playing (str)   
    ennemy_team : name of the ennemy_team (str)

    Return :
    --------
    end : sets the game to finished depending on the structure points or number of pacific rounds (bool)
    
    Notes : 
    -------
    This function gets the end_counter from the attack function to verify end_counter >= 40 if yes end = True, else False
    It also gets the strucure points of each hub to verify structure points (hub) <= 0 if yes end = True, else False

    Versions
    --------
    specification : Kevin Schweitzer (v.1 24/02/20)
                    Anthony Pierard (v.2 10/03/20)
    
    """  
    #at beginning end is false
    end = False
    winner = 'NO'

    #check if 40 rounds have passed
    if end_counter >= 40:
        end = True

        #Verify wich team has the most health point
        if units_stats[team]['hub']['HP'] < units_stats[ennemy_team]['hub']['HP'] :
            winner = ennemy_team 
        elif  units_stats[team]['hub']['HP'] > units_stats[ennemy_team]['hub']['HP'] :
            winner = team 
        else: 
            winner = 'NO'

    #Verify if there is a winner => if someone has 0 HP
    elif int(units_stats[team]['hub']['HP']) <= 0: 
        end = True
        winner = team 
    elif int(units_stats[ennemy_team]['hub']['HP']) <= 0:
        end = True
        winner = ennemy_team

    return end, winner

def separate_instruction (order, ships, units_stats,board,team,peaks):
    """ 
    Separate the different instrcution in the order and separate the first part of the instruction from the second ( on the left of the ':' and then on the right ) and set it in a list with all the other instructions
    
    Parameter
    ---------
    order: order of the player (str)
    ships :  dictionnary with the statistics of each ship (tanker or cruiser)(dict)
    units_stats :dictionnary with the stats (different or common) of the teams (hub /ship) (dict)
    board : dictionary where each coordinates gives a list of entities on this position (dict)
    team : name of the team which is playing (str)   
    peaks : dictionnary with all the peaks (dict) 
    
    Return
    ------
    instructions_list : list with all the instrcution separate in two (list) 
    
    Notes 
    -----
    3 steps : 
        - split the instructions of the order
        - split the instructions in two part (in a list)
        - set the all the list in the instrcutions_list
    
    Version 
    -------
    specification : Johan Rochet (v.1 22/02/20)
                    Pierre Merveille (v.2 27/02/20)
                    Johan Rochet (v.3 20/03/20)
    implementation : Johan Rochet (v.1 20/03/20)
                     Kevin Schweitzer (v.2 22/03/20)
    """
    upgrade_list = []
    create_list = []
    move_list= []
    attack_list= []
    transfer_list = []
    x_list =[]
    y_list =[]
    instructions_list= []
    

    # list the coordinates of the board to check after if the instrcutions are correct
    for key in board :
        # add the x-coordinates in x_list 
        if not str(key[0]) in x_list :
            x_list.append(str(key[0]))
        # add the y-coordinates in y_list 
        if not str(key[1]) in y_list :
            y_list.append (str(key[1]))
       
    # cut the different instrcutions
    order_list = order. split (' ')
    instructions_list = []
    # cut the instruction in two part around the ':' if there is only one ':'
    for instruction in order_list :
        #check if there is only one ':'
        occurence = 0
        for element in instruction :
            if element == ':' :
                occurence += 1
        #add to instrcution_list if there is only one ':'
        if occurence == 1: 
            instruction = instruction.split (':')
            instructions_list.append(instruction)
        
       
    
    # determine the nature of the instruction and set it in a list if it's correct
    for order in instructions_list:
        if order[1] != '' :  
           
        # check if it's an upgrade-instruction
            correct = False
            if order[0] == 'upgrade' :
                if order[1] == 'regeneration' or order[1] == 'range' or order[1] == 'move' or order[1] == 'storage':
                    upgrade_list.append(order[1])
            
            # check if order[0] is a ship    
            elif order[0] in ships and ships[order[0]]['team'] == team :            
            
                
                # check if there is only one '-'in order[1]
                occurence = 0
                for element in order[1] : 
                    if element == '-':
                        occurence += 1
                # if there is only one '-', cut the coorinates in 2 round the '-'      
                if occurence == 1:              
                    coordinates = order[1][1:].split('-')
                    # if it's an attack-instruction ==> handle with the attack_value (ex: *10-12=23)
                    if order[1][0] == '*':
                        value= False
                        # check if there is only one '=' in coordinates[1]
                        occurence= 0
                        for element in coordinates[1] :

                            if element == '=':
                                occurence += 1
                        # if there is only one '=', cut the coorinates[1] in 2 round the '=' 
                        if occurence ==1 : 
                            coordinate_y = coordinates[1].split('=')
                            #set the y-coordinate of the attack in coordinate[1]
                            coordinates[1] = coordinate_y[0]
                        
                    # verify if the coordinates are in the board
                    if coordinates[0] in x_list and coordinates[1] in y_list :
                        correct = True
                #add to the move_list if it's a correct move 
                if order[1][0] == '@' and correct :
                    move_list.append([order[0], order[1][1:]])
                # add to the attack_list if it's a correct attack
                elif order[1][0] == '*'and correct:
                    attack_list .append([order[0], order[1][1:]])
                # add to the transfer_list if it's a good transfer
                elif order[1][0] == '<' :
                    if order[1][1:] == 'hub' or correct :
                        if correct :
                            
                            peak_list =[]
                            for peak in peaks :
                                peak_list. append (peaks[peak]['coordinates'])
                            if (int(coordinates[0]),int(coordinates[1])) in peak_list :
                                transfer_list.append([order[0],order[1]])
                        else : 
                            transfer_list.append([order[0],order[1]])
                                        
                elif order[1][0] == '>' :
                    if order[1][1:] == 'hub' or order[1][1:] in ships:
                        transfer_list.append([order[0],order[1]])

            # add to the create_list if it's a creation
            elif (order[1]== 'tanker'or order[1]== 'cruiser') and order[0] not in ships :
                create_list.append([order[0], order[1]])

    return upgrade_list , create_list, move_list, attack_list, transfer_list
    
def create_units (create_list, ships, team, board, units_stats, peaks) :
    
    """ Creates new units in the team either a tanker or a cruiser and place it on the board
    
    Parameters
    ----------
    create_list : list of create order (list)
    ships :  dictionnary with the statistics of each ship (tanker or cruiser)(dict)
    team : name of the team which is playing (str)   
    board : dictionnary with the coordinates of all boxes of the board which gives a list of element on this place (dict)
    units_stats :dictionnary with the stats (different or common) of the teams (hub /ship) (dict)
    peaks : the dictionnary with all the peaks (dict)
    
        
    Returns :
    --------
    ships : dictionnary with the new added ship (dict)
    board : dictionnary with the coordinates of all boxes of the board which gives a list of element on this place (dict)
    units_stats :dictionnary with the stats (different or common) of the teams (hub /ship) (dict)

    
    Notes : 
    -------
    This function will add a new ship in ships(dict) using the team. 
    It will determinate if the ship the player want to create is a cruiser or a tanker and gives it different attributes depending on its type
    Hub will always be shown on board but adds new ship to the list of entities on this position ( display_order : hub --> ship --> tanker)
    
    Versions
    --------
    specification : Johan Rochet (v.1 20/02/20)
                    Pierre Merveille (v.2 10/03/20)
    implementation : Johan Rochet (v.1 01/03/20) 
                     Johan Rochet (V.2 15/03/20)
     
    """
   
    #carries out orders.
    for instruction in create_list :

        #Take the coordinates from the hub
        coordinates = units_stats[team]['hub']['coordinates']
        
        #verify wich type of ship has to be create and and if there are enough enrgy point in the hub
        if (instruction[1]== 'tanker' or instruction[1] == 'cruiser') and  units_stats[team]['hub']['energy_point'] >= units_stats['common'][instruction[1]]['creation_cost'] :
            
            #Get the energy point of the ship
            if instruction[1]== 'tanker' :
                energy_point = units_stats[team][instruction[1]]['max_energy'] 
            else : 
                energy_point = units_stats['common'][instruction[1]]['max_energy']

            #Get the other stat of the ship and create it and put it on the board
            max_HP = units_stats['common'][instruction[1]]['max_HP'] 
            ships[instruction[0]]= {'coordinates': coordinates , 'HP': max_HP, 'energy_point' : energy_point, 'type' : instruction[1], 'team' : team}
            board[coordinates]['list_entity'].append(instruction[0])
            change_value('hub',ships, peaks,-units_stats['common'][instruction[1]]['creation_cost'],'energy_point',units_stats,team)

    return ships,board,units_stats
    
def upgrade (upgrade_list, team, units_stats, ships, max_upgrade, cost_upgrade):
   
    """ 
    Permanently upgrade units or hub caracteristics 
    
    Parameters
    ----------
    upgrade_list : list of the upgrade order (list)
    team : name of the team which is playing (str)   
    units_stats :dictionnary with the stats (different or common) of the teams (hub /ship) (dict)
    ships :  dictionnary with the statistics of each ship (tanker or cruiser)(dict)
    max_upgrade : dictionary containing the values for each upgrade (dict)
    cost_upgrade : dictionary containing the price for each upgrade (dict)
    
    Return
    ------
    units_stats : update stats in dictionnary (dict)

    Notes
    -----
    Need to verify if player/team asking the upgrade has enough energy stored for this upgrade in their hub reserves. If false upgrade denied, If True upgrade       
  
    range : modify cruiser range by adding max_range_upgrade to the range in units_stats associated to the team asking the upgrade  
    move : modify cruiser move by max_travel_upgrade to the move in units_stats associated to the team asking the upgrade
    storage : modify tanker max_energy by adding max_capacity_upgrade to the max_energy in units_stats associated to the team asking the upgrade
    regeneration : modify hub regeneration per round by adding max_regen_upgrade to the regen in units_stats associated to the team asking the upgrade
       
    
    Versions
    --------
    specification : Kevin Schweitzer (v.1 20/02/20)
                    Anthony Pierard (v.2 28/02/20)
    implementation : Kevin Schweitzer (v.1 20/02/20)
                     Kevin Schweitzer (v.2 1/03/20)
   
    """
    #verify for each team if they have enough energy in hub to do the requested upgrade
    #example for upgrade_list = ['regeneration', 'storage', 'move','range']
    #get upgrade_cost for requested upgrades

    #carries out orders.
    for upgrade in upgrade_list:

            #if team has enough energy do requested upgrades, else print('caps(%s): you don't have enough energy stored in your hub')%team
            if upgrade == 'regeneration':
                
                if units_stats[team]['hub']['regeneration'] < max_upgrade['max_regen_upgrade']:
                
                    if cost_upgrade['cost_regen_upgrade']  <= units_stats[team]['hub']['energy_point']:
                        units_stats[team]['hub']['regeneration'] += 5
                        units_stats[team]['hub']['energy_point'] -= 700

            elif upgrade == 'storage':
                storage_cost = cost_upgrade['cost_upgrade_capacity']
                
                if units_stats[team]['tanker']['max_energy'] < max_upgrade['max_capacity_upgrade']:
                    
                    if storage_cost <= units_stats[team]['hub']['energy_point']:
                        units_stats[team]['tanker']['max_energy'] += 100
                        units_stats[team]['hub']['energy_point'] -= 600           
            
            elif upgrade == 'move':
                move_cost = cost_upgrade['cost_travel_upgrade']

                if units_stats[team]['cruiser']['move'] > max_upgrade['max_travel_upgrade']:

                    if move_cost <= units_stats[team]['hub']['energy_point']:
                        units_stats[team]['cruiser']['move'] -= 1
                        units_stats[team]['hub']['energy_point'] -= 500

            elif upgrade == 'range':
                range_cost = cost_upgrade['cost_range_upgrade']
                
                if units_stats[team]['cruiser']['range'] < max_upgrade['max_range_upgrade']:
                    
                    if range_cost <= units_stats[team]['hub']['energy_point']:
                        units_stats[team]['cruiser']['range'] += 1
                        units_stats[team]['hub']['energy_point'] -= 400
    return units_stats
                        
def attack (attack_list, board, units_stats, ships, team, ennemy_team, peaks, end_counter,color_team):
    
    """Execute an attack on a chosen box
    
    Parameters
    ----------
    attack_list : order from the attack_list (list)
    board : dictionnary with the coordinates of all boxes of the board which gives a list of element on this place (dict)
    units_stats :dictionnary with the stats (different or common) of the teams (hub /ship) (dict)
    ships :  dictionnary with the statistics of each ship (tanker or cruiser)(dict)
    team : name of the team which is playing (str)
    ennemy_team : name of the ennemy_team (str)
    peaks : the dictionnary with all the peaks (dict)
    end_counter : number of rounds without attacks (float)
    color_team : dictionnary with the number of the team with the color of each team (dict)
    
    Returns
    -------
    end_counter : number of rounds without attacks (float)
    
    Notes
    -----
    Change the statut of the ship
    
    Versions
    --------
    specification : Anthony Pierard (v.1 20/02/20)
                    Anthony Pierard (v.2 13/03/20)
    implementation : Anthony Pierard (v.1 03/02/20)
                     Pierre Merveille (v.2 27/02/20)
    """                       
    #Implementation of the function attack
    #Initialise the coordinate and the attack point
    #attack_point = coord_attack[1]
    if len(attack_list)==0:
        end_counter+=0.5
        
    else :
            #carries out orders.
        for instruction in attack_list :
            
            coord_attack=instruction[1].split('=')
            #coord_attack[1]= attack_point
            coordinates= coord_attack[0].split ('-')
            #coordinates = tuple (x,y)
            coordinates = (int(coordinates[0]),int(coordinates[1]))
            #verify in another function if we have the range
            hithin_range = range_verification (units_stats, instruction[0], ships, coordinates, team)
            #create a list for delete cruiser
            cruiser_dead=[]
            position=[]
            #create a variable verify if something is hit
            hit=0
            #attack if hithin_range is True
            print(coord_attack)
            if hithin_range and ships[instruction[0]]['energy_point']>=int(coord_attack[1]):
                #reduce the energy of the ship
                ships = change_value(instruction[0], ships, peaks, int(coord_attack[1])*-1, 'energy_point', units_stats, team)
                #verify the coordinates of all the ship
                for ship in ships :
                    if ships[ship]['coordinates']==coordinates:
                        #change the value of the point of structure of the ship in the coordinate
                        ships = change_value(ship, ships, peaks, int(coord_attack[1])*-1, 'HP', units_stats, ennemy_team)
                        hit+=1
                        end_counter=0
                        
                        
                        if ships[ship]['HP']<=0:
                            #stock a dead cruiser
                            cruiser_dead.append(ship)
                for team_name in color_team: 
                #verify if the is in the coordinates
                    if units_stats[team_name]['hub']['coordinates']==coordinates :
                        #change the value of the point of structure of the hub in the coordinate
                        untis_stats=change_value('hub', ships, peaks, int(coord_attack[1])*-1, 'HP', units_stats, team_name)
                        hit+=1
                        end_counter=0 
                           
                    #if units_stats[team]['hub']['HP']<=0:
                if hit==0 : 
                    #if nothing is hit than increment the end_counter
                    end_counter += 0.5
                   
                    
            else :
                end_counter += 0.5
            #delete the ships which are destroyed
            for ship in cruiser_dead:
                    index = board[ships[ship]['coordinates']]['list_entity'].index(ship)
                    del (board[ships[ship]['coordinates']]['list_entity'][index])
                    del ships[ship]   
    return end_counter
    
def move (move_list, ships, team, board, units_stats, peaks) :
    
    """ Move a ship on the board
    
    Parameters
    ----------
    move_list : order from the move_list (list)
    ships :  dictionnary with the statistics of each ship (tanker or cruiser)(dict)
    team : name of the team which is playing (str)
    board : dictionnary with the coordinates of all boxes of the board which gives a list of element on this place (dict)
    units_stats :dictionnary with the stats (different or common) of the teams (hub /ship) (dict)
    peaks : parameter of change_value (dict)
        
    Return :
    --------
    ships :  dictionnary with the statistics of each ship (tanker or cruiser)(dict)
    board : dictionnary with the coordinates of all boxes of the board which gives a list of element on this place (dict)
    
    Notes : 
    -------
    This function moves a ship to the chosen position
    
    Versions
    --------
    specification : Pierre Merveille (v.1 20/02/20)
                    Johan Rochet (v.1 27/02/20)
    implementation : Pierre Merveille (v.1 2/03/20)
    
    """  
    #carries out orders.
    for instruction in move_list:
            #get the oler and the new coordinates
            new_coord = instruction[1].split('-')
            new_coord = (int(new_coord[0]), int(new_coord[1]))
            old_coord = ships[instruction[0]]['coordinates']

            #Verify if the ship can go to the new coordinates
            if max (abs(new_coord[0]-old_coord[0]), abs(new_coord[1]-old_coord[1])) < 2 :

                #Verify if the ship is a tanker
                if ships[instruction[0]]['type'] == 'tanker':

                    #change coordinates of moved tanker
                    change_value(instruction[0], ships, peaks, new_coord, 'coordinates', units_stats, team)

                    #Put the tanker to his new coordinates on the board and delete is older coordinates
                    board[new_coord]['list_entity'].append(instruction[0])
                    index = board[old_coord]['list_entity'].index(instruction[0])
                    del board[old_coord]['list_entity'][index]

                else:
                    #Verify if the cruiser have enough energy_point
                    if ships[instruction[0]]['energy_point'] > max(abs(new_coord[0] - old_coord[0]), abs(new_coord[1] - old_coord[1])) * units_stats[team]['cruiser']['move'] :
                        
                        #Update the stat of the cruiser
                        change_value(instruction[0], ships, peaks, ( - (max(abs(new_coord[0] - old_coord[0]), abs(new_coord[1] - old_coord[1])) * units_stats[team]['cruiser']['move'])), 'energy_point', units_stats,team)
                        change_value(instruction[0], ships, peaks, new_coord, 'coordinates', units_stats, team)

                        #Put the tanker to his new coordinates on the board and delete is older coordinates
                        board[new_coord]['list_entity'].append(instruction[0])
                        index = board[old_coord]['list_entity'].index(instruction[0])
                        del board[old_coord]['list_entity'][index]
                
    return board, ships
            
def change_value ( entity_name, ships, peaks, new_value, caracteristic, units_stats, team):
    
    """
    Change the value of one of the caracteristic of the ship or the peak
    
    Parameters
    ----------
    entity_name : name of the entity for which you want to change a value (str)
    ships :  dictionnary with the statistics of each ship (tanker or cruiser)(dict)
    peaks : dictionnary with all the peaks (dict)
    new_value : number of point to change (positive or negative) (int)
    caracteristic : caractrestic you want to change the value with the quantity (str)
    units_stats :dictionnary with the stats (different or common) of the teams (hub /ship) (dict)
    team : name of the team which is playing (str)
    
    Return 
    ------
    units_stats :dictionnary with the stats (different or common) of the teams (hub /ship) (dict)
    or 
    ships :  dictionnary with the statistics of each ship (tanker or cruiser)(dict)
    or 
    peaks : the dictionnary with the change of value for the caracteristic (dict)
    
    Notes 
    -----
    This function change a cracteristic of a ship, a peak or a hub and return a different dictionnary depending on the change
    
    Version 
    -------
    specification : Johan Rochet (v.1 22/02/20)
                    Anthony Pierard (v.2 01/03/20)
    implémentation : Anthony Pierard (v.1 01/03/20)
                     Anthony Pierard (v.2 04/03/20)

    
    """   
    
    #implementation of the function change value
    #change value for the hub

    if entity_name == 'hub' :
        #change the value in function of the caracteristic and return the dictionnary
        units_stats[team]['hub'][caracteristic] += new_value
        return units_stats
    else :
        #change the value for the ship 
        for ship in ships :
            #check all the name of the ship in ships
            if entity_name == ship :
                #condition if it's a coordinates because new_value is a tuple
                if caracteristic == 'coordinates' :
                    ships[entity_name]['coordinates'] = new_value
                else :
                    ships[entity_name][caracteristic] += new_value
                return ships
        #change value for the peak
        for peak in peaks:
            #check all the name of the peak in peaks
            if entity_name == peak :
                #condition if it's a coordinates because new_value is a tuple
                if caracteristic == 'coordinates' :
                    peaks[entity_name]['coordinates'] = new_value
                else :
                    peaks[entity_name]['storage'] += new_value
                return peaks
      
def transfer (transfer_list, ships, team, units_stats, peaks, board) :

    """ 
    Fill a tanker's energy storage into a cruiser or into the hub 
    OR
    Fill the storage of a tanker with the energy of a peak or a hub

    Parameters
    ----------
    transfer_list : list of the transfer order (list)
    ships :  dictionnary with the statistics of each ship (tanker or cruiser)(dict)
    team : name of the team which is playing (str)   
    units_stats :dictionnary with the stats (different or common) of the teams (hub /ship) (dict)
    peaks : dictionnary with all the peaks (dict)
    board : dictionnary with the coordinates of all boxes of the board which gives a list of element on this place (dict)

    Return :
    --------
    ships :  dictionnary with the statistics of each ship (tanker or cruiser)(dict)
    units_stats :dictionnary with the stats (different or common) of the teams (hub /ship) (dict) 
    peaks : dictionnary with the new or not value of storage of a peak (dict)

    Notes : 
    -------
    This function can place the energy of a tanker into a cruiser or into the hub 
    But it can also place the storage_energy of a peak into a tanker

    Versions
    --------
    specification : Pierre Merveille (v.1 24/02/20)
                    Pierre Merveille (v.2 10/03/20)
    implementation: Johan Rochet (v.1 01/03/20)
                    Johan ROchet (v.2 15/03/20)
    """    
    # draw energy
    for instruction in transfer_list :
        if instruction [1][0] == '<':
            
            if ships[instruction[0]]['type'] == 'tanker':
                # in_dico = storage of the tanker 
                in_dico = ships[instruction[0]]['energy_point']
                # max_storage  = max stroage of a tanker 
                max_storage = units_stats[team]['tanker']['max_energy']
            # set all to 0 if it isn't a tanker 
            else :
                max_storage = 0
                in_dico = 0
                       
            #if the tanker draw energy in a peak 
            
            if not instruction [1][1:] == 'hub' :
                # split and store the coordinates if it's a peak 
                instruction[1] = instruction[1][1:].split ('-')
                instruction[1][0] = int(instruction[1][0])
                instruction[1][1] = int(instruction[1][1])
                instruction[1] = tuple (instruction[1])
                           
                for peak in peaks : 
                    if peaks[peak]['coordinates'] == instruction[1] :
                        
                        #transfer energy 
                        if max_storage > in_dico and range_verification(units_stats, instruction[0], ships,instruction[1],team ):
                            print (in_dico)
                            print (max_storage)
                            print (type(peaks[peak]['storage']))
                            while in_dico < max_storage and peaks[peak]['storage'] >0 :
                    
                                in_dico += 1
                                peaks[peak]['storage'] -= 1
            #if the tanker draw energy in a hub
            elif instruction [1][1:] == 'hub' :
                out_dico =units_stats[team]['hub']['energy_point']
                #transfer energy
                if max_storage > in_dico and units_stats[team]['hub']['energy_point'] >0 and range_verification(units_stats, instruction[0], ships,units_stats[team]['hub']['coordinates'],team ):
                   
                    while in_dico < max_storage and units_stats[team]['hub']['energy_point'] >0 :
                    
                        in_dico += 1
                        units_stats[team]['hub']['energy_point'] -= 1
            if ships[instruction[0]]['type'] == 'tanker':
                ships[instruction[0]]['energy_point'] = in_dico
                    
        #--------------------------------------------------------------------------------------------------------
        
        #give energy  to a ship or the hub    
        elif instruction [1][0] == '>' :
            
            if ships[instruction[0]]['type'] == 'tanker' :
                out_dico = ships[instruction[0]]['energy_point']
                
                if  instruction[1][1:] == 'hub' :
                    if range_verification(units_stats, instruction[0], ships,units_stats[team][instruction[1][1:]]['coordinates'], team) :
                    
                        while units_stats[team][instruction[1][1:]]['energy_point'] < units_stats['common']['hub']['max_energy_point'] and ships[instruction[0]]['energy_point'] > 0 :

                            ships[instruction[0]]['energy_point'] -=1 
                            units_stats[team][instruction[1][1:]]['energy_point'] += 1
                #give energy to a cruiser
                elif ships[instruction[1][1:]]['type']== 'cruiser' : 
                    if range_verification(units_stats, instruction[0], ships,ships[instruction[1][1:]]['coordinates'], team) :
                    
                        while ships[instruction[1][1:]]['energy_point'] < units_stats['common']['cruiser'] ['max_energy'] and ships[instruction[0]]['energy_point'] > 0:
                            
                            ships[instruction[1][1:]]['energy_point'] += 1 
                            ships[instruction[0]]['energy_point'] -= 1
                    #give energy to a hub    
                
    return ships, units_stats , peaks
def round_end (board, end_counter, units_stats, peaks, elements, color_team, ships):

    """ Print new board and stats and make "end of round changes" and do the regeneration of the hub energy
    
    Parameters  
    ----------
    
    board : dictionnary with the coordinates of all boxes of the board which gives a list of element on this place (dict)
    end_counter : number of rounds without attacks (float)
    units_stats :dictionnary with the stats (different or common) of the teams (hub /ship) (dict)
    peaks : dictionnary with all the peaks (dict) 
    elements : character for each type of entity (dict)
    color_team : dictionnary with the number of the team with the color of each team (dict)
    ships :  dictionnary with the statistics of each ship (tanker or cruiser)(dict)

    Return :
    --------
    units_stats :dictionnary with the stats (different or common) of the teams (hub /ship) (dict)
    
    Notes : 
    -------
    This function changes the energy amount for each hub at the end of every round. The function also prints the board with all changes made during the current round.
    This function uses other fuctions like change_value, display_board and display_stats to display the board and stats after each rounds changes.

    Versions
    --------
    specification : Kevin Schweitzer (v.1 24/02/20)
    
    implémentation : Kevin Schweitzer (v.1 01/03/20)
    
    """    
    #add energy to hub every round end
    for team in color_team:
        if units_stats[team]['hub']['energy_point'] + units_stats[team]['hub']['regeneration'] < units_stats['common']['hub']['max_energy_point']:
            change_value('hub', ships, peaks, units_stats[team]['hub']['regeneration'], 'energy_point', units_stats, team)
        
    #display board every round end
    board_display(board, color_team, ships, peaks, units_stats, elements)

    #display stats every round end
    display_stats (elements, color_team, ships, units_stats, peaks)
    return units_stats
    
def select_value_to_print (board, coordinates, units_stats, ships, peaks, color_team, elements):
    """
    Select the character to print on the board  and its color

    Parameters
    ----------
    board : dictionnary with the coordinates of all boxes of the board which gives a list of element on this place (dict)
    coordinates : tuple with the coordinate of the box (tuple)
    units_stats :dictionnary with the stats (different or common) of the teams (hub /ship) (dict)
    ships :  dictionnary with the statistics of each ship (tanker or cruiser)(dict)
    peaks : dictionnary with all the peaks (dict)
    color_team : dictionnary with the number of the team with the color of each team (dict)
    elements : dictionnary with the type of entity (cruiser, hub,...) with the charactere of each type (dict)
    
    Return
    ------
    value_to_print : character to print on a box with its color

    Version:
    --------
    specification : Johan Rochet (v1. 28/02/20)
                    Johan Rochet (v.2 06/04/20)
    implementation : Johan Rochet (v1. 28/02/20)
                     Johan Rochet (v2. 15/03/20)
    """
    
    if board[coordinates]['list_entity'] == ['   '] :
                
        value_to_print = ('   ')
        
    else : 
                
        value_to_print = [4]
        # select the units to display and the color of it. Order = hub-cruiser-tanker-peak
        for entity in board[coordinates]['list_entity']: 
                       
            # first verifiy if the entity is a hub        
            if entity in units_stats : 
                # set O, the color of the hub and the type of the entity in value_to_print 
                value_to_print = [0,color_team[entity], 'hub']
                
            # then check if it's a ship  
            elif entity in ships: 
                #check if it's a cruiser
                if ships[entity]['type'] == 'cruiser':
                    # verify that ther is no hub already placed
                    if value_to_print[0] >0 :
                        # set 1, the color of the cruiser and the type of the entity in value_to_print
                        value_to_print = [1,color_team[ships[entity]['team']],'cruiser']
                #check if it's a tanker        
                else : 
                    # verify that ther is no hub or cruiser  already placed
                    if value_to_print[0] >1 :
                        # set 2, the color of the tanker and the type of the entity in value_to_print
                        value_to_print = [2,color_team[ships[entity]['team']],'tanker']
            # finally check if it' a peak 
            elif entity in peaks : 
                # verify that ther is no hub, cruiser or tanker already placed
                if value_to_print[0] > 2 :
                    # set 2 and the color 'yellow' in value_to_print
                    value_to_print = [3, fg(10)+ attr(1), 'peak']
        # center the character in the box
        value_to_print[2] = ' '+ elements[value_to_print[2]] + ' '
        value_to_print = value_to_print[1] + value_to_print[2]
   
    return value_to_print
    
def board_display ( board, color_team, ships, peaks, units_stats, elements) :
    """ 
    Display the board 

    Parameters 
    ----------
    board : dictionnary with the coordinates of all boxes of the board which gives a list of element on this place (dict)
    color_team : dictionnary with the number of the team with the color of each team (dict)
    ships :  dictionnary with the statistics of each ship (tanker or cruiser)(dict)
    peaks : dictionnary with all the peaks (dict)
    units_stats :dictionnary with the stats (different or common) of the teams (hub /ship) (dict)   
    elements : dictionnary with the type of entity (cruiser, hub,...) with the charactere of each type (dict)

    Notes : 
    -------

    This function create boxes in a "damier" so that the players can easily see the difference between each boxes
    The board is surrounded by a "bordure" which contains the numbers of the boxes as when you play chess 

    Version 
    -------
    specification : Johan Rochet (v.1 22/02/20)
                    Anthony Pierard (v.2 01/03/20)
                    Johan Rochet (v.3 06/04/20)
    implémentation : Anthony Pierard (v.1 01/03/20)
                    Johan Rochet (v.2 03/03/20)
                    
    """
    larg = 0
    long = 0
    bord = fg(255)
    for coordinates in board :
        if coordinates[1] > larg :
            larg = coordinates[1]
        if coordinates[0] > long :
            long = coordinates[0]
    # creation of the board
    for i in range (larg+2):
        #jump for each row
        bord += bg(0) + '\n'
        
        if i == 0 or i == larg +1 :
            #first and last row
            for j in range (long+2):
                #begin
                if j == 0 :
                    bord += bg('6')+'   ' 
                #end
                elif j == long+1 :
                    bord+= bg('6') +'   '
                #column < 10        
                elif j<10:
                    bord+= bg(6)+str(j) +'  '
                #column < 100   
                else :
                    bord += bg(6) + str(j)+ ' '
            
        else : 
            
            #intermediate rows
            for j in range (long+2):
                #begin and end
                if j==0 or j==long+1:
                    bord += bg('6') + str(i) 
                    if i<10 : 
                        #begin
                        bord+= '  '
                    else:
                        #end
                        bord += ' '+ bg('0')
                else :
                    #grid
                    if (i+j) % 2 == 0 :
                        color= bg('231')
                    else : 
                        color = bg('115')
                    # add the character and the front color of the character and reset color to white after
                    bord += color + select_value_to_print(board, (j,i),units_stats,ships,peaks, color_team,elements)  + attr(0) + fg('255')
    bord += bg('0')       
    print(bord) 
        
def display_stats (elements, color_team, ships, units_stats, peaks):
    """
    Displays the statistics of all the ships, peaks and hubs
    
    Parameters
    ----------
    elements : dictionnary with the type of entity (cruiser, hub,...) with the charactere of each type (dict)
    color_team : dictionnary with the number of the team with the color of each team (dict)
    ships :  dictionnary with the statistics of each ship (tanker or cruiser)(dict)
    units_stats :dictionnary with the stats (different or common) of the teams (hub /ship) (dict)
    peaks : dictionnary with all the peaks (dict) 
    
    Notes 
    -----
    This function displays the statistics of the peaks, the hub and all the ship on the board so that the player knows wich ship is placed on which boxes
    This function is only there to help the player managing/memorising the environnement, the name and all the stats of the ships in his own team as in the adverse team
    
    Version 
    -------
    specification : Johan Rochet (v.1 22/02/20)
    implementation : Kevin Schweitzer (v.1 28/02/20)
                     Kevin Schweitzer et Johan Rochet (v.2 03/03/20)
    
    """
    #color legend for each team
    print('\n')
    for element in color_team :
        print (color_team[element] + '[' + str(element) + '] : \u2588\u2588') 
    #change color back to white

    ##############HUBS#################
    print(fg(255)+'\nHUBS')
    print('------------------------------')
    #for each team get hub stats
    for team_name in color_team : 
        stats = units_stats[team_name]['hub']
        
        #for each hub display stats
        hub_stats = color_team[team_name]
        for stat in stats :
            
            value = str(stats[stat])
            if stat == 'coordinates':
                stat = '⯐ '

            elif stat == 'HP':
                stat = '❤ '

            elif stat == 'energy_point':
                stat = '⚡  '

            elif stat == 'regeneration':
                stat = '🔌  '

            hub_stats += stat +': ' + value + '   '    
        
        print(hub_stats)

    ##############Peaks###############
    print(fg(255)+'\nPEAKS')
    print('------------------------------')
    #for each peak get stats
    for stat in peaks : 
        stats = peaks[stat]

        #for each peak display stats
        peak_stats = ''
        for stat in stats :
            
            value = str(stats[stat])
            if stat == 'coordinates':
                stat = '⯐ '

            elif stat == 'storage':
                stat = '⚡  '

            peak_stats += stat + ': ' + value + '   '    

        print(peak_stats)

    ##############SHIPS################
    print(fg(255)+'\nSHIPS')
    print('------------------------------')
    #for each team get tanker stats from units_stats
    for team_name in color_team:
        team_stats = units_stats[team_name]['tanker']
        common_stats = units_stats['common']['tanker']  
        
        #for each tanker get stats from ships 
        for tanker in ships : 
            if ships[tanker]['type'] == 'tanker': #verify it's a tanker
            
                for ship in ships:
                
                    ship_stats = ships[ship]
                
                    for team_stat in team_stats:
                    
                        value = str(team_stats[team_stat])
                        if team_stat == 'max_energy':
                            stat_team = color_team[team_name] + '💼  ' 
                        tanker_stats_1 = stat_team +': ' + value + '   '         
                    
                    for common_stat in common_stats :

                        value = str(common_stats[common_stat])
                        if common_stat == 'creation_cost':
                            stat_common = color_team[team_name] + '💵  '
                            
                        elif common_stat == 'move':
                            stat_common = '⛽ '

                        tanker_stats_2 = stat_common +': ' + value + '  '
                        
                    for ship_stat in ship_stats:

                        value = str(ship_stats[ship_stat])
                        if ship_stat == 'coordinates':
                            stat_ship = color_team[team_name] + '⯐ '
                        
                        elif ship_stat == 'team':
                            stat_ship = '👤 '

                        elif ship_stat == 'type':
                            stat_ship = 'ѧ/ѫ'
                        
                        elif ship_stat == 'HP':
                            stat_ship = '❤ '

                        elif ship_stat == 'energy_point':
                            stat_ship = '⚡  '

                        tanker_stats_3 = stat_ship +': ' + value + '  '

    #get common stats from unit_stats
    common_stats = units_stats['common'] 
    for type in common_stats:
        #put common stats in different variables (tanker_common or cruiser_common)
        if  type == 'tanker':

            value = str (common_stats[type]['creation_cost'])
            tanker_common = ' | $:' + value

            value = str (common_stats[type]['move'])
            tanker_common += ' | ⛽ :' + value

        elif type == 'cruiser':
            
            value = str (common_stats[type]['creation_cost'])
            cruiser_common = ' | $:' + value

            value = str (common_stats[type]['cost_attack'])
            cruiser_common += ' | $/\u204c :' + value

            value = str (common_stats[type]['attack'])
            cruiser_common += ' | \u204c :' + value

            value = str (common_stats[type]['max_energy'])
            cruiser_common += ' | Max⚡ :' + value

            

    tanker_common += ' ]'
    cruiser_common += ' ]'                    

    team_stats ={}
    #for each team get tanker and cruiser stats depending on team
    for team_name in color_team:
            
        tanker_stats = units_stats[team_name]['tanker']
        cruiser_stats = units_stats[team_name]['cruiser']
        
        #for each key change icon and associate it to value
        value = str(tanker_stats['max_energy'])
        tanker_team_stats = ' | \U0001F50B :' + value

        value = str(cruiser_stats['range'])
        cruiser_team_stats  = ' | \u2B57 :' + value

        value = str (cruiser_stats['move'])
        cruiser_team_stats += ' | ⛽ :' + value

        team_stats[team_name] = {'cruiser_stats' : cruiser_team_stats, 'tanker_stats' : tanker_team_stats }
        
    ship_cruiser_stats =''
    ship_tanker_stats = ''

    ship_team ={}
    for team in color_team :
        ship_team[team] = {'cruiser' : [], 'tanker': []}

    for ship in ships:
        ship_stats = ship 

        value = str(ships[ship]['coordinates'])
        ship_stats += ': [ a :' + value
        
        value = str(ships[ship]['HP'])
        ship_stats += ' | ❤ :' + value
        
        value = str(ships[ship]['energy_point'])
        ship_stats += ' | ⚡  :' + value

        if ships[ship]['type'] == 'cruiser':
            value = elements['cruiser']
            ship_cruiser_stats = ship_stats + ' | type :' + value 
            ship_team[ships[ship]['team']]['cruiser'].append(ship_cruiser_stats) 
            
        elif ships[ship]['type'] == 'tanker':
            value = elements['tanker']
            ship_tanker_stats = ship_stats + ' | type :' + value 
            ship_team[ships[ship]['team']]['tanker'].append(ship_tanker_stats)

    #for each team get cruiser and tanker info from list in ship_team
    for team in color_team: 
        print(color_team[team])
        
        for cruiser in ship_team[team]['cruiser']:
            print(cruiser + team_stats[team]['cruiser_stats'] + cruiser_common)
        
        for tanker in ship_team[team]['tanker']:
            print(tanker + team_stats[team]['tanker_stats'] + tanker_common)

    print(fg(255))   
    
def range_verification (units_stats, ship_name, ships, coordinates, team):

    """  Verify if the ship can attend the box 

    Parameters
    ----------
    units_stats :dictionnary with the stats (different or common) of the teams (hub /ship) (dict)
    ship_name : name of the ship (str)
    ships :  dictionnary with the statistics of each ship (tanker or cruiser)(dict)
    coordinates : coordinates of the box to attend (tuple)
    team : name of the team which is playing (str)   

    Return 
    ------
    whithin_range : true if coordinates are in range and False if not (bool)

    Notes
    -----
    This function is used for the move of the cruiser and the trnasfer of the tanker to verify if the coordinates are within the range of them (for the tanker: range = 1)

    Versions
    --------
    specification : Johan Rochet (v.1 24/02/20)
    implémentation : Anthony Pierard (v.1 27/02/20)
                     Pierre Merveille (v.2 12/03/20)
    """

    #Verify the range
    if max (abs(coordinates[0]-ships[ship_name]['coordinates'][0]), abs(coordinates[1]-ships[ship_name]['coordinates'][1])) <= units_stats[team]['cruiser']['range'] :
        
        return True
    else :
        return False

def create_order(long, larg,  team, ships, units_stats,peaks) :

    """ This function create the order for the IA

    Parameter :
    ----------
    long : length of the board  (int)
    larg : width of the board (int)
    team : name of the team which is playing (str)   
    ships :  dictionnary with the statistics of each ship (tanker or cruiser)(dict)
    units_stats :dictionnary with the stats (different or common) of the teams (hub /ship) (dict)
    peaks : dictionnary with all the peaks (dict) 

    Return : 
    --------
    AI_order : order from the AI

    Notes :
    --------
    Create random order for the IA

    Versions
    --------
    specification : Pierre Merveille (v.1 24/02/20)
                    Johan Rochet (v.2 14/03/20)
    implémentation : Johan rochet / Pierre Merveille (v1 25/03/20)
                     Anthony Pierard / Kevin schweitzer (v2 25/03/20)
    """

    #Set the variable
    nb_order = randint(1,30)
    order_list = []
    instruction_list =[]
    create_unit = {'tanker' : 0, 'cruiser' : 0}
    cruiser_list=[]
    tanker_list = []
    peak_coordinates =[]

    #count the number of cruiser
    for ship in ships :

        if ships[ship]['type'] == 'cruiser' and ships[ship]['team'] == team : 
            cruiser_list.append(ship)
        
    #count the number of cruiser
    for ship in ships :

        if ships[ship]['type'] == 'tanker' and ships[ship]['team'] == team : 
            tanker_list.append(ship)
        
    #Get the peaks coordinates
    for peak in peaks :
        peak_coordinates.append (peaks[peak]['coordinates'])
    
    ship_list = tanker_list+ cruiser_list
    
    #get the type of the order to each order
    while nb_order != 0 :
        order = choice(['move', 'create','transfer','attack', 'upgrade'])
        order_list.append(order)
        nb_order -= 1
   
    for order in order_list :
        #create a ship

        if order == 'create' :
            instruction = choice(['tanker','cruiser'])
            if instruction == 'tanker' :
                type_list = tanker_list 
            else :
                type_list = cruiser_list

            #verify if a ship is already done or not                
            if len(type_list) == 0 :

                #Add the order  
                instruction_list.append(instruction + '_'+ str(team) +'_' + str(create_unit[instruction]) + ':' + instruction)
            else:
                number_tanker = (len(type_list) +create_unit[instruction])

                #Add the order  
                instruction_list.append( instruction + '_'+ str(team) +'_' + str(str(number_tanker)) + ':' + instruction)
                
            create_unit[instruction]+= 1
                        
        #transfer energy 
        elif order == 'transfer' and tanker_list != [] and peak_coordinates != []:
            order_type = choice(['draw','give'])
            
            #Verify if it s energy point draw or give
            if order_type == 'draw' :

                    #Select a tanker and make a draw      
                    tanker = choice(tanker_list)
                    coordinates = []
                    output = choice(['hub','peak'])
                    if output == 'peak' :
                        coordinates= choice (peak_coordinates)

                        #Add the order  
                        instruction_list.append(tanker + ':<' +str(coordinates[0]) + '-'+ str(coordinates[1]))
                    else : 
                        instruction_list.append(tanker + ':<hub')    
            else:
               
                #Select a tanker and give energy point for a hub or a cruiser    
                tanker = choice(tanker_list)
                coordinates = []
                Input = choice(['hub','ship'])

                if Input == 'hub' :
                        instruction_list.append(tanker + ':>hub')
                else : 
                    if cruiser_list !=[] :

                        cruiser = choice(cruiser_list)
                        coordinates = ships[cruiser]['coordinates']

                        #Add the order      
                        instruction_list.append(tanker + ':>' + str(coordinates[0]) + '-'+ str(coordinates[1]))

        #Attack
        elif order == 'attack' and cruiser_list != [] :

            #Attack to a random coordinate
            cruiser = choice(cruiser_list)
            x=randint(1,long)
            y=randint(1,larg)
            damage=randint(0 ,ships[cruiser]['energy_point'])

            #Add the order  
            instruction_list.append(str(cruiser) + ':' + str(x) + '-' + str(y) + '=' + str(damage))

        #Move          
        elif order == 'move' and ship_list != [] :

            #Move to a random coordinate        
            ship_in_movement= choice(ship_list)
            line = randint(0,long)
            column = randint(0,larg)

            #Add the order  
            instruction_list.append(ship_in_movement + ':@' + str(line) + '-' + str(column))

        #Upgrade
        elif order == 'upgrade' :

            #Get a upgrade stat
            order_type = choice(['regeneration', 'storage', 'move', 'range'])
            instruction_list.append('upgrade:' + order_type)

    instruction_str = ''
    for element in instruction_list :
        instruction_str += element +' '
    
    return instruction_str
