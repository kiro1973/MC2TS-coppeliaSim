#######THE LAST VERSION OF DRAWING THE wind in areas and still remaining is changing BG color of wind to match the background but it is good
import math
import threading
from coppeliasim_zmqremoteapi_client import RemoteAPIClient
import os
import time
from PyQt5.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QLabel, 
    QVBoxLayout, 
    QWidget,
    QHBoxLayout,
    QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QPen
import sys
from simulation.utils.config import *
from simulation.utils.circleWidget import CircleWidget

script_dir = os.path.dirname(os.path.abspath(__file__))



class DroneSimulation(QThread):
    energy_updated = pyqtSignal(float)
    
    def __init__(self, points, wind_regions):  # Changed from wind_moves to wind_regions
        super().__init__()
        self.client = RemoteAPIClient()
        self.sim = self.client.getObject('sim')
        self.is_hi_mode = False
        self.accumulated_cost_mode_LO = 0
        self.accumulated_cost_mode_HI = 0
        self.points = points
        script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the script's directory
        self.red_bluetooth = os.path.join(script_dir, 'img', 'bluetooth_red.png')
        self.black_bluetooth = os.path.join(script_dir, 'img', 'bluetooth_black.png')
        self.wind_icon_path = os.path.join(script_dir, 'img', 'wind_icon_2.png')
        self.wind_cirle_path = os.path.join(script_dir, 'img', 'wind_circle.png')
        self.wind_regions = wind_regions  # Now expects list of regions
        self.energy = 100
        self.move_count = 0
        self.quadcopter_handle = None
        self.sensors = {}
        self.wind_region_handles = []  # Stores handles for wind regions
        self.wind_icon_handles =[]
        self.consumed_energy = 0
        self.previous_sensor = None
        self.initialize_simulation()

    def initialize_simulation(self):
        self.quadcopter_handle, self.sensors = self.create_coords(self.points)
        # Create wind region visualizations
        
        for region in self.wind_regions:
            handle = self.create_wind_region(region['center'], region['radius'])
            self.wind_region_handles.append(handle)
            self.sim.setObjectInt32Param(handle, self.sim.objintparam_visibility_layer, 0)

        print("Simulation initialized with wind regions.")

    
    def create_wind_icon(self, center, scale=[0.3, 0.3, 0.01]):
        print('I created a wind icon')
        icon_handle = self.sim.createPrimitiveShape(
            self.sim.primitiveshape_plane, scale, 0)
        self.sim.setObjectPosition(icon_handle, -1, [center[0], center[1], 1.0])
        shape, texture_id, _ = self.sim.createTexture(self.wind_icon_path, 0, None, None)
        self.sim.setShapeTexture(
            icon_handle, texture_id, self.sim.texturemap_plane, 0, [1, 1])
        return icon_handle
    



    def create_wind_region(self, center, radius):
        print(f"created wind regionwith center: {center}")
        """Create a horizontal circle outline with wind icon using a thin cylinder"""
        # Create a thin cylinder for the perimeter
        cylinder = self.sim.createPrimitiveShape(
            self.sim.primitiveshape_plane,
            [radius*2,radius*2, 0.02],  # Explicitly set radii and thin height
            0
        )

        self.sim.setObjectPosition(cylinder, -1, [center[0], center[1], 0.9])

        shape, texture_id, _ = self.sim.createTexture(self.wind_cirle_path, 0,  None, None)
        self.sim.setShapeTexture(
            cylinder, texture_id, self.sim.texturemap_plane, 0, [radius*2,radius*2])

        return cylinder


    def calculate_intersection(self, start, end, center, radius):
        """Calculate distance through a circular region"""
        x1, y1 = start
        x2, y2 = end
        cx, cy = center
        
        dx = x2 - x1
        dy = y2 - y1
        a = dx**2 + dy**2
        if a == 0: return 0.0
        
        b = 2 * (dx*(x1 - cx) + dy*(y1 - cy))
        c = (x1 - cx)**2 + (y1 - cy)**2 - radius**2
        disc = b**2 - 4*a*c
        
        if disc < 0: return 0.0
        
        sqrt_disc = math.sqrt(disc)
        t1 = (-b - sqrt_disc) / (2*a)
        t2 = (-b + sqrt_disc) / (2*a)
        t_start = max(0.0, min(t1, t2))
        t_end = min(1.0, max(t1, t2))
        
        if t_start >= t_end: return 0.0
        return (t_end - t_start) * math.hypot(dx, dy)

    def get_consumed_energy(self):
        return self.consumed_energy

    def get_remaining_energy(self):
        return self.energy

    def is_in_wind_region(self, position, move_count):
        for region in self.wind_regions:
            if move_count in region["moves"]:
                distance = math.sqrt((position[0] - region["center"][0])**2 + (position[1] - region["center"][1])**2)
                if distance <= region["radius"]:
                    return True
        return False

    def calculate_energy_consumption(self, base_energy, start_pos, end_pos, move_count):
        total_distance = math.sqrt((end_pos[0] - start_pos[0])**2 + (end_pos[1] - start_pos[1])**2)
        wind_distance = 0
        no_wind_distance = total_distance

        for region in self.wind_regions:
            if move_count in region["moves"]:
                # Calculate the intersection of the drone's path with the wind region
                # This is a simplified calculation; you may need a more accurate method
                distance = math.sqrt((end_pos[0] - region["center"][0])**2 + (end_pos[1] - region["center"][1])**2)
                if distance <= region["radius"]:
                    wind_distance += total_distance
                    no_wind_distance -= total_distance

        energy_consumed = (no_wind_distance * coef_energy_no_wind_real) + (wind_distance * coef_energy_wind_real)
        return energy_consumed

    def create_label(self, object_handle, label_text, is_critical=False):
        try:
            object_position = self.sim.getObjectPosition(object_handle, -1)
            color = [1, 0, 0] if is_critical else [0, 0, 0]
            
            text_shape = self.sim.generateTextShape(
                label_text, color, 0.15, True
            )
            label_position = [
                object_position[0] + 0.07,
                object_position[1] + 0.07,
                object_position[2] + 0.01
            ]
            self.sim.setObjectPosition(text_shape, -1, label_position)
        except Exception as e:
            print(f"Error creating label for object {object_handle}: {e}")

    def create_plane(self, center_x, center_y, width, height):
        # Create a smaller plane by reducing the width and height
        plane_handle = self.sim.createPrimitiveShape(
            self.sim.primitiveshape_cuboid,  
            [width, height, 0.01],  # Keep the original dimensions from parameters
            0
        )
        self.sim.setObjectPosition(plane_handle, -1, [center_x, center_y, -0.005])

        darker_green = [0.2, 0.68, 0.2]  # Much darker shade of green
        self.sim.setShapeColor(plane_handle, None, 0, darker_green)
        
        return plane_handle
    def create_bluetooth_icon(self, position, is_critical):
        # Create a small plane for the bluetooth icon
        icon_scale = [0.3, 0.3, 0.3]  # Smaller scale for bluetooth icon
        icon_handle = self.sim.createPrimitiveShape(
            self.sim.primitiveshape_plane, icon_scale, 0
        )
        
        # Position the icon slightly above the sensor
        icon_position = [
            position[0]+0.4,
            position[1]+0.4,
            position[2] + 0.2  # Slightly above the sensor
        ]
        self.sim.setObjectPosition(icon_handle, -1, icon_position)
        
        # Choose icon based on whether the sensor is critical
        icon_path = self.red_bluetooth if is_critical else self.black_bluetooth
        shape, texture_id, _ = self.sim.createTexture(icon_path, 0, None, None)
        self.sim.setShapeTexture(
            icon_handle, texture_id, self.sim.texturemap_plane, 0, [1, 1]
        )
        return icon_handle

    def create_quadcopter(self, position):
        quadcopter_handle = self.sim.loadModel('models/robots/mobile/Quadcopter.ttm')
        self.sim.setObjectPosition(quadcopter_handle, -1, position)
        return quadcopter_handle

    def create_vision_sensor(self, position):
        options = 0 | 4
        intParams = [256, 256, 0, 0]
        floatParams = [0.01, 10.0, 60.0 * (math.pi / 180), 0.05,
                      0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        sensor_handle = self.sim.createVisionSensor(options, intParams, floatParams)
        self.sim.setObjectPosition(sensor_handle, -1, position)
        return sensor_handle

    def remove_default_floor(self):
        try:
            floor_handle = self.sim.getObject('/Floor')
            box_handle = self.sim.getObject('/Floor/box')
            self.sim.removeObjects([floor_handle, box_handle], False)
        except Exception:
            pass

    def resize_existing_floor(self, sensor_positions):
        self.remove_default_floor()
        min_x = min(pos[0] for pos in sensor_positions)
        max_x = max(pos[0] for pos in sensor_positions)
        min_y = min(pos[1] for pos in sensor_positions)
        max_y = max(pos[1] for pos in sensor_positions)
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        width = max_x - min_x + 2
        height = max_y - min_y + 2
        # Create a smaller plane by adding less padding
        plane_handle = self.create_plane(center_x, center_y, width + 4, height + 4)  # Reduced padding from 10 to 4
        return plane_handle

    def create_coords(self, points):
        # Create floor based on all points
        sensor_positions = [(data["x"], data["y"]) for key, data in points.items()]
        self.resize_existing_floor(sensor_positions)
        
        # Create quadcopter at position B
        quadcopter_position = [points["B"]["x"], points["B"]["y"], 2]
        quadcopter_handle = self.create_quadcopter(quadcopter_position)
        
        # Create sensors and bluetooth icons for all points
        sensors = {}
        for key, data in points.items():
            sensor_position = [data["x"], data["y"], 1]
            sensor_handle = self.create_vision_sensor(sensor_position)
            self.sim.setObjectAlias(sensor_handle, key)
            
            is_critical = data.get('c', False)
            label_shape=self.create_label(sensor_handle, key, is_critical)
            
            # Create bluetooth icon for each sensor
            bluetooth_handle = self.create_bluetooth_icon(sensor_position, is_critical)
            # Optionally store the bluetooth handle if you need to modify it later
            sensors[key] = {
                'sensor': sensor_handle,
                'bluetooth': bluetooth_handle,
                'label':label_shape
            }

        return quadcopter_handle, sensors



    def mark_label_visited(self, sensor_name, is_critical): ##COLORING
        try:
            print(f"/{sensor_name}[1]/text")
            text_shape = self.sim.getObject(f"/{sensor_name}[1]/text")
           
            # Soft light red for critical sensors
            soft_red = [1, 1, 1]  
            # Soft gray for non-critical sensors
            soft_gray = [1, 1, 1]
            
            color = soft_red if is_critical else soft_gray
            
            self.sim.setObjectColor(text_shape, 0, self.sim.colorcomponent_ambient_diffuse, color)
            #self.sim.setShapeColor(text_shape, None, 0, color)
        except Exception as e:
            print(f"Error marking label visited: {e}")
    def mark_label_visited_text(self, sensor_name, is_critical): ##COLORING
        try:
            print(f"/{sensor_name}[1]/")
            text_shape = self.sim.getObject(f"/{sensor_name}[1]")
            text_shape_inner_text = self.sim.getObject(f"/{sensor_name}[1]/text")
            print ("the object i got: ",text_shape )
            object_position = self.sim.getObjectPosition(text_shape, -1)
            self.sim.removeObject(text_shape)
            self.sim.removeObject(text_shape_inner_text)
            visited_string=sensor_name+ " v"
            # Soft light red for critical sensors
            color = [1, 0, 0] if is_critical else [0, 0, 0]
            
            text_shape = self.sim.generateTextShape(
                visited_string, color, 0.17, True
            )
            label_position = [
                object_position[0] + 0.0,
                object_position[1] + 0.0,
                object_position[2] + 0.0
            ]
            self.sim.setObjectPosition(text_shape, -1, label_position)
        except Exception as e:
            print(f"Error marking label visited_2: {e}")
    def color_drone_mode_if_HI(self,isHi):
        drone_circle_shape = self.sim.getObject("/Quadcopter/base/target")
        soft_red = [0.8, 0.0, 0.0]  
        # Soft gray for non-critical sensors
        soft_gray = [0.0, 0.1, 0.9]
        color = soft_red if isHi else soft_gray
        self.sim.setObjectColor(drone_circle_shape, 0, self.sim.colorcomponent_ambient_diffuse, color)

    def move_drone_to_sensor(self, sensor_name, is_HI_Mode, acc_cost_hi, acc_cost_lo):
        self.color_drone_mode_if_HI(is_HI_Mode)
        time.sleep(0.5)
        self.move_count += 1
        self.is_hi_mode = is_HI_Mode
        self.accumulated_cost_mode_LO = acc_cost_lo
        self.accumulated_cost_mode_HI = acc_cost_hi
        # Update wind region visibility
        for i, region in enumerate(self.wind_regions):
            handle = self.wind_region_handles[i]
            if self.move_count in region['moves']:
                self.sim.setObjectInt32Param(handle, self.sim.objintparam_visibility_layer, 1)
            else:
                self.sim.setObjectInt32Param(handle, self.sim.objintparam_visibility_layer, 0)

        # Calculate path energy consumption
        prev_point = self.points.get(self.previous_sensor, self.points["B"])
        current_point = self.points[sensor_name]
        start = [prev_point['x'], prev_point['y']]
        end = [current_point['x'], current_point['y']]
        total_dist = math.hypot(end[0]-start[0], end[1]-start[1])
        
        wind_dist = 0.0
        active_regions = []
        for region in self.wind_regions:
            if self.move_count in region['moves']:
                region_dist = self.calculate_intersection(start, end, region['center'], region['radius'])
                
                print("calculate_intersection returned: ",region_dist)
                if region_dist > 0:
                    wind_dist += region_dist
                    active_regions.append({
                        'center': region['center'],
                        'radius': region['radius'],
                        'distance': region_dist
                    })

        energy_used = (wind_dist * coef_energy_wind_real + 
                    (total_dist - wind_dist) * coef_energy_no_wind_real)
        
        # Add detailed print output
        print(f"\n=== Move {self.move_count} to {sensor_name} ===")
        print(f"Total distance: {total_dist:.2f} units")
        if wind_dist > 0:
            print(f"Passed through {len(active_regions)} wind region(s):")
            for i, region in enumerate(active_regions, 1):
                print(f"  Region {i}: Center {region['center']}, Radius {region['radius']}")
                print(f"    Wind distance: {region['distance']:.2f} units")
            print(f"Total wind distance: {wind_dist:.2f} units")
            print(f"Normal distance: {total_dist - wind_dist:.2f} units")
        else:
            print("No wind regions encountered")
        
        print(f"Energy cost calculation:")
        print(f"  Wind distance ({wind_dist:.2f}) * {coef_energy_wind_real} = {wind_dist * coef_energy_wind_real:.2f}W")
        print(f"  Normal distance ({total_dist - wind_dist:.2f}) * {coef_energy_no_wind_real} = {(total_dist - wind_dist) * coef_energy_no_wind_real:.2f}W")
        print(f"Total energy cost: {energy_used:.2f}W")
        
        self.consumed_energy += energy_used
        self.energy -= (energy_used / init_energy * 100)
        self.energy_updated.emit(self.energy)

        # Rest of movement logic
        target_pose = self.sim.getObjectPose(self.sensors[sensor_name]['sensor'], -1)
        target_pose[2] += 1.0
        self.sim.moveToPose({
            'object': self.quadcopter_handle,
            'targetPose': target_pose,
            'maxVel': [0.05]*4,
            'maxAccel': [0.05]*4,
            'maxJerk': [0.1]*4,
            'relativeTo': -1
        })

        sensor_data = self.sensors.get(sensor_name)
        text_shape = sensor_data['label']
        is_critical = self.points[sensor_name].get('c', False)
        
        # Mark label as visited
        self.mark_label_visited(sensor_name, is_critical)
        
        self.previous_sensor = sensor_name
        print("is_HI_Mode_simu", is_HI_Mode)
        print("Move to sensor : ", sensor_name)
        print("accumulated_cost_mode_LO", acc_cost_lo)
        print("accumulated_cost_mode_HI", acc_cost_hi)
        print("real_consumed_energy",self.consumed_energy)
        print("real_remaining_energy",self.energy)