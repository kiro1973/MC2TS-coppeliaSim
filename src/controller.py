import matplotlib.pyplot as plt
import sys
import threading
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal
from simulation.simulation import DroneSimulation
from simulation.utils.droneMonitor import DroneMonitor
from simulation.utils.energyWindow import EnergyWindow
from simulation.utils.config import *
class PlotSignals(QObject):
    plot_signal = pyqtSignal(dict, list, list, list)
class DroneController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.energy_window = EnergyWindow()
        self.simulation = None
        self.monitor = None
        self.algorithm_thread = None
        self.plot_signals = PlotSignals()
        self.plot_signals.plot_signal.connect(self.plot_in_main_thread)
        
    def initialize(self):
        self.simulation = DroneSimulation(points, wind_regions)
        self.simulation.energy_updated.connect(self.energy_window.update_energy)
        self.monitor = DroneMonitor(self.simulation, self.energy_window)
        self.monitor.start()
        
    def plot_in_main_thread(self, points_data, visited_sensors, deleted_sensors, is_HI_Mode_list):
        self.plot_capteurs_points(points_data, visited_sensors, deleted_sensors, is_HI_Mode_list)
    def plot_capteurs_points(self,points, real_visited_sensors, deleted_sensors, is_HI_Mode_list):
        plt.clf()
        plt.gcf().set_size_inches(10, 8) 
        # Tracer les capteurs
        for name, coord in points.items():
            x, y = coord["x"], coord["y"]
            if name in deleted_sensors:  # Si le capteur est supprimé
                plt.scatter(x, y, color="gray", marker="x", label="Ignored Sensor" if "Ignored Sensor" not in plt.gca().get_legend_handles_labels()[1] else "", s=100)
            elif name == "B":  # Base
                plt.scatter(x, y, color="black", marker="o", label="Base" if "Base" not in plt.gca().get_legend_handles_labels()[1] else "", s=100)
            elif name in critical_sensors:  # Capteurs critiques
                plt.scatter(x, y, color="red", marker="o", label="Critical Sensor" if "Critical Sensor" not in plt.gca().get_legend_handles_labels()[1] else "", s=100)
            elif name in non_critical_sensors:  # Capteurs non-critiques
                plt.scatter(x, y, color="green", marker="o", label="Non-Critical Sensor" if "Non-Critical Sensor" not in plt.gca().get_legend_handles_labels()[1] else "", s=100)
            
            # Ajouter les étiquettes des capteurs
            offset_x = 0.3
            plt.text(x + offset_x, y, name, fontsize=10, ha='left', va='center')

        if real_visited_sensors:
            label_hi_mode_shown = False
            label_lo_mode_shown = False 
            for i in range(len(real_visited_sensors) - 1):  # Parcourt les segments
                sensor_start = real_visited_sensors[i]
                sensor_end = real_visited_sensors[i + 1]
                color = "orange" if is_HI_Mode_list[i] else "gray"
                if is_HI_Mode_list[i] and not label_hi_mode_shown:
                    label = "Drone Motion in HI Mode"
                    label_hi_mode_shown = True
                elif not is_HI_Mode_list[i] and not label_lo_mode_shown:
                    label = "Drone Motion in LO Mode"
                    label_lo_mode_shown = True
                else:
                    label = None 
                # Récupérer les coordonnées de départ et d'arrivée pour le segment
                x_coords_segment = [points[sensor_start]["x"], points[sensor_end]["x"]]
                y_coords_segment = [points[sensor_start]["y"], points[sensor_end]["y"]]

                # Tracer le segment avec la couleur appropriée
                plt.plot(x_coords_segment, y_coords_segment, color=color, linestyle="--", marker="o", label=label if label else "")
                
                # Ajouter une flèche sur le premier segment
                if i == 0:
                    x_arrow = x_coords_segment[0] + (x_coords_segment[1] - x_coords_segment[0]) * 0.75
                    y_arrow = y_coords_segment[0] + (y_coords_segment[1] - y_coords_segment[0]) * 0.75
                    plt.annotate(
                        "", 
                        xy=(x_arrow, y_arrow), 
                        xytext=(x_arrow - (x_coords_segment[1] - x_coords_segment[0]) * 0.05, y_arrow - (y_coords_segment[1] - y_coords_segment[0]) * 0.05), 
                        arrowprops=dict(arrowstyle="->", color=color, lw=2, mutation_scale=20)
                    )

        plt.title("Position des capteurs et de la base")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.grid(True)
        plt.axhline(0, color="black", linewidth=0.5)
        plt.axvline(0, color="black", linewidth=0.5)
        plt.legend()
        plt.draw()
        plt.pause(0.1)
        
    def run_algorithm(self, algorithm_function):
        self.algorithm_thread = threading.Thread(
            target=lambda: algorithm_function(self.simulation, self.plot_signals)
        )
        self.algorithm_thread.daemon = True
        self.algorithm_thread.start()
    
    def start(self):
        try:
            self.app.exec_()
        finally:
            if self.monitor:
                self.monitor.stop()
                self.monitor.join()