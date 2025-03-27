from random import choice
from my_MCTS import MCTS, Node 
import math

from simulation.utils.config import *
from simulation.simulation import DroneSimulation
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal
import threading
import time
from controller import DroneController
import matplotlib
matplotlib.use('Qt5Agg')

is_HI_Mode = False



class Node(Node):
    next_node_id = 0

    def __init__(self, sensor, parent, terminal):
        self.id = Node.next_node_id
        Node.next_node_id +=1
        self.sensor = sensor 
        self.parent = parent
        self.terminal = terminal
        self.accumulated_cost_mode_LO = 0 
        self.accumulated_cost_mode_HI = 0
        self.compute_accumulated_cost()

    def compute_accumulated_cost(self):
        if (self.parent == None):
            self.accumulated_cost_mode_LO = 0 
            self.accumulated_cost_mode_HI = 0 
        else:
            dist_from_parent_to_current_node = calculate_distance(points[self.parent.sensor], points[self.sensor])
            self.accumulated_cost_mode_LO = self.parent.accumulated_cost_mode_LO + coef_energy_no_wind_max*dist_from_parent_to_current_node
            
            if (points[self.sensor]["c"] == True):
                node = self.parent
                worst_previous_node = self.parent
                worst_accumulated_cost = node.accumulated_cost_mode_HI
                while (node.parent != None and points[node.sensor]["c"]==False):
                    node = node.parent
                    if (node.accumulated_cost_mode_HI > worst_accumulated_cost):
                        worst_accumulated_cost = node.accumulated_cost_mode_HI
                        worst_previous_node = node

                    """dist_to_compare = calculate_distance(points[node.sensor], points[self.sensor])
                    if (dist_to_compare > longest_dist_from_previous_to_curent_node):
                        longest_dist_from_previous_to_curent_node = dist_to_compare 
                    """                  
                dist_from_previous_node_with_worst_accumulated_cost = calculate_distance(points[worst_previous_node.sensor], points[self.sensor])
                self.accumulated_cost_mode_HI = worst_accumulated_cost + coef_energy_wind_max*dist_from_previous_node_with_worst_accumulated_cost
            else:
                self.accumulated_cost_mode_HI = self.parent.accumulated_cost_mode_LO + coef_energy_wind_max*dist_from_parent_to_current_node

    def find_children(self):
        if self.terminal:
            return set()
        
        visited_sensors = set()
        node = self
        while (node.parent != None):
            visited_sensors.add(node.sensor)
            node = node.parent 

        unvisited_sensors = [
            sensor for sensor in points.keys() if sensor not in visited_sensors and sensor != "B"
        ]

        if (len(unvisited_sensors) != 0):
            return {
                    self.choose_next_sensor(sensor) for sensor in unvisited_sensors
            }
        else : #Gestion du cas où on a visité tous les capteurs 
            return {
                    self.choose_next_sensor("B") 
            }
    
    def find_closer_child(self):
        if self.terminal:
            return None
        visited_sensors = set()
        node = self
        while (node.parent != None):
            visited_sensors.add(node.sensor)
            node = node.parent

        unvisited_sensors = [
            sensor for sensor in points.keys() if sensor not in visited_sensors and sensor != "B"
        ]

        min_distance = float("inf")
        closest_sensor = "B"
        for un_sensor in unvisited_sensors:
            distance = calculate_distance(points[self.sensor], points[un_sensor])
            if distance < min_distance:
                min_distance = distance 
                closest_sensor = un_sensor
        return self.choose_next_sensor(closest_sensor)

    def is_terminal(self):
        return self.terminal

    def reward(self):
        if not self.terminal:
            raise RuntimeError(f"reward called on nonterminal self {self}")
        else:
            total_dist = calculate_accumulated_distance_drone(self)
            max_dist = calculate_distance_totale_max()
            
            reward = 0
            total_nber_sensors_ET_poids = (len(critical_sensors)*reward_critical_sensors + len(non_critical_sensors)*reward_non_critical_sensors)
            node = self
            while (node.parent != None):
                sensor = node.sensor
                if sensor in critical_sensors:
                    reward += reward_critical_sensors/total_nber_sensors_ET_poids
                else:
                    reward += reward_non_critical_sensors/total_nber_sensors_ET_poids
                node = node.parent 
            reward -= (reward_non_critical_sensors/total_nber_sensors_ET_poids)*(total_dist/max_dist)
            return reward
    
    def choose_next_sensor(self, sensor):

        temp_node = Node(sensor = sensor, parent = self, terminal = False)
        temp_child = Node(sensor="B", parent=temp_node, terminal = True)

        #Gestion du cas où on a visité tous les capteurs 
        if (sensor == "B"): 
            return Node(sensor = sensor, parent = self, terminal = True)
        
        #Dans le cas où il n'y a jamais de vent on parcourt la sequence entière ! 
        #Si on met la condition d'arrêt de la sequence avec HI, on optimise pas du tt l'énergy du drone... (il reste plein d'énergy à la fin...)
        #elif (self.accumulated_cost_mode_LO + coef_energy_no_wind*(dist_to_next+dist_next_to_base) >= init_energy ):  
        
        elif temp_child.accumulated_cost_mode_HI <= init_energy : 
            return temp_node
        else : 
            return Node(sensor = "B", parent = self, terminal = True)


def calculate_distance(capteur1, capteur2):
    x1, y1 = capteur1['x'], capteur1['y']
    x2, y2 = capteur2['x'], capteur2['y']
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def calculate_accumulated_distance_drone(last_node):
    accumulated_dist = 0 
    node = last_node
    while (node.parent != None):
        accumulated_dist += calculate_distance(points[node.sensor], points[node.parent.sensor])
        node = node.parent 
    return accumulated_dist

def calculate_distance_totale_max():
    remaining = points.copy()
    current = remaining.pop("B")
    total = 0
    while remaining:
        next_name, next_point = max(remaining.items(), key=lambda p: calculate_distance(current, p[1]))
        total += calculate_distance(current, next_point)
        current = remaining.pop(next_name)
    return total





def do_drone_navigation(simulation, plot_signals):
    global is_HI_Mode

    tree = MCTS()
    node = Node(sensor="B", parent=None, terminal=False)
    sensors_since_last_replanning = 0
    visited_sensors = []
    real_visited_sensors =[]
    deleted_sensors = []
    visited_sensors.append(node.sensor)
    real_visited_sensors.append(node.sensor)
    is_HI_Mode_list = []
    
    while True:
        if node.terminal:
            break
            
        if sensors_since_last_replanning >= 3 or node.parent == None:
            for _ in range(nber_of_rollout_iterations):
                tree.do_rollout(node)
            sensors_since_last_replanning = 0
            print("Do algo")




        #Move to next node 
        node = tree.choose(node)
        visited_sensors.append(node.sensor)
        sensors_since_last_replanning += 1

        #Déplacement ou delete en fonction du mode du current node
        if (is_HI_Mode):
            if(points[node.sensor]["c"] == True):
                simulation.move_drone_to_sensor(node.sensor, is_HI_Mode, node.accumulated_cost_mode_HI, node.accumulated_cost_mode_LO)
                real_visited_sensors.append(node.sensor)
                is_HI_Mode_list.append(is_HI_Mode)
                #Mise à jour accumulated cost (cause deleted node) !! FAUX ???????????
                #node.compute_accumulated_cost() 

                #Mise à jour du mode
                real_energy_consumed = simulation.get_consumed_energy()
                if (real_energy_consumed > node.accumulated_cost_mode_LO):
                    is_HI_Mode = True
                else : 
                    is_HI_Mode = False
            else :
                deleted_sensors.append(node.sensor)

        else:
            simulation.move_drone_to_sensor(node.sensor, is_HI_Mode, node.accumulated_cost_mode_HI, node.accumulated_cost_mode_LO)
            real_visited_sensors.append(node.sensor)
            is_HI_Mode_list.append(is_HI_Mode)
            
            #Mise à jour du mode
            real_energy_consumed = simulation.get_consumed_energy()
            if (real_energy_consumed > node.accumulated_cost_mode_LO):
                is_HI_Mode = True
            else : 
                is_HI_Mode = False

        
        time.sleep(0.1)

    #PRINT
    dist_to_go = calculate_distance(points[node.parent.sensor], points[node.sensor])
    print("dist_from_parent_to_current",dist_to_go)
    print(f"Capteurs visités : {visited_sensors}")
    print(f"Capteurs visités (réel): {real_visited_sensors}")
    print(f"Deleted sensor :  {deleted_sensors}")
    print("energy_consumed_LO", node.accumulated_cost_mode_LO, node.sensor)
    print("energy_consumed_HI", node.accumulated_cost_mode_HI, node.sensor)
    print("real_energy_consumed", real_energy_consumed)
    print("is_HI_Mode", is_HI_Mode)


    

    print(f"Nombre de capteurs visités : {len(visited_sensors)}")
    opti_total_dist = calculate_accumulated_distance_drone(node)
    print(f"Distance totale parcourue par le drône (opti) : {opti_total_dist}")
    energy_remaining = init_energy - real_energy_consumed
    print(f"Energy restante drône : {energy_remaining}")
    print(f"Final Reward : ", node.reward())
    plot_signals.plot_signal.emit(points, real_visited_sensors, deleted_sensors, is_HI_Mode_list)

if __name__ == "__main__":
    controller = DroneController()
    controller.initialize()
    controller.run_algorithm(do_drone_navigation)
    controller.start()