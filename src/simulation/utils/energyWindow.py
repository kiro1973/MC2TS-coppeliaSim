
from simulation.utils.circleWidget import CircleWidget
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from simulation.utils.config import *
class EnergyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drone Energy Monitor")
        self.setFixedSize(350, 500)
        
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width()-380, 110)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Energy header section (battery icon and labels)
        energy_header = QWidget()
        energy_layout = QHBoxLayout(energy_header)
        
        battery_label = QLabel()
        battery_pixmap = QPixmap("battery.png").scaled(40, 40, Qt.KeepAspectRatio)
        battery_label.setPixmap(battery_pixmap)
        energy_layout.addWidget(battery_label)
        
        energy_labels = QWidget()
        energy_text_layout = QVBoxLayout(energy_labels)
        
        self.energy_label = QLabel(f"Remaining: 100%")
        self.initial_energy_label = QLabel(f"Initial: {init_energy} W")
        
        self.energy_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.initial_energy_label.setStyleSheet("font-size: 12px; color: #666;")
        
        energy_text_layout.addWidget(self.energy_label)
        energy_text_layout.addWidget(self.initial_energy_label)
        energy_layout.addWidget(energy_labels)
        
        layout.addWidget(energy_header)
        
        # Mode and cost section
        self.mode_label = QLabel("Mode: LO")
        self.mode_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.mode_label.setStyleSheet("font-size: 14px; font-weight: bold; color: blue;")
        layout.addWidget(self.mode_label)
        
        self.cost_lo_label = QLabel("Acc. Cost (LO): 0.00 W")
        self.cost_hi_label = QLabel("Acc. Cost (HI): 0.00 W")
        self.consumed_energy_label = QLabel("Consumed Energy: 0.00 W")
        
        for label in [self.cost_lo_label, self.cost_hi_label, self.consumed_energy_label]:
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            label.setStyleSheet("font-size: 12px;")
            layout.addWidget(label)
        
        # Add first separator line
        first_separator = QFrame()
        first_separator.setFrameShape(QFrame.HLine)
        first_separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(first_separator)
        
        # Position section
        self.position_label = QLabel("Position:")
        self.position_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.position_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.position_label)
        
        self.x_label = QLabel("X: 0.00")
        self.y_label = QLabel("Y: 0.00")
        self.z_label = QLabel("Z: 0.00")
        for label in [self.x_label, self.y_label, self.z_label]:
            label.setStyleSheet("font-size: 12px;")
            layout.addWidget(label)
        
        # Add second separator line
        second_separator = QFrame()
        second_separator.setFrameShape(QFrame.HLine)
        second_separator.setFrameShadow(QFrame.Sunken)
        second_separator.setLineWidth(2)
        layout.addWidget(second_separator)
        
        # Legend section with side-by-side layout
        legend_label = QLabel("Legend:")
        legend_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(legend_label)
        
        # Create a widget to hold both legends side by side
        legends_container = QWidget()
        legends_layout = QHBoxLayout(legends_container)
        legends_layout.setContentsMargins(0, 0, 0, 0)
        
        # === SENSORS LEGEND (LEFT SIDE) ===
        sensors_widget = QWidget()
        sensors_layout = QVBoxLayout(sensors_widget)
        sensors_layout.setContentsMargins(5, 5, 5, 5)
        
        sensors_title = QLabel("Sensors:")
        sensors_title.setStyleSheet("font-weight: bold;")
        sensors_layout.addWidget(sensors_title)
        
        # Critical sensor indicator
        critical_sensor = QWidget()
        critical_layout = QHBoxLayout(critical_sensor)
        critical_layout.setContentsMargins(0, 0, 0, 0)
        critical_circle = CircleWidget('red')
        critical_layout.addWidget(critical_circle)
        critical_text = QLabel("Critical sensor")
        critical_layout.addWidget(critical_text)
        critical_layout.addStretch()
        sensors_layout.addWidget(critical_sensor)
        
        # Normal sensor indicator
        normal_sensor = QWidget()
        normal_layout = QHBoxLayout(normal_sensor)
        normal_layout.setContentsMargins(0, 0, 0, 0)
        normal_circle = CircleWidget('black')
        normal_layout.addWidget(normal_circle)
        normal_text = QLabel("Normal sensor")
        normal_layout.addWidget(normal_text)
        normal_layout.addStretch()
        sensors_layout.addWidget(normal_sensor)
        
        # Visited sensor indicator
        visited_sensor = QWidget()
        visited_layout = QHBoxLayout(visited_sensor)
        visited_layout.setContentsMargins(0, 0, 0, 0)
        visited_circle = CircleWidget('white')
        visited_layout.addWidget(visited_circle)
        visited_text = QLabel("Visited sensor")
        visited_layout.addWidget(visited_text)
        visited_layout.addStretch()
        sensors_layout.addWidget(visited_sensor)
        
        legends_layout.addWidget(sensors_widget)
        
        # === DRONE MODE LEGEND (RIGHT SIDE) ===
        drone_mode_widget = QWidget()
        drone_mode_layout = QVBoxLayout(drone_mode_widget)
        drone_mode_layout.setContentsMargins(5, 5, 5, 5)
        
        drone_mode_title = QLabel("Drone Mode:")
        drone_mode_title.setStyleSheet("font-weight: bold;")
        drone_mode_layout.addWidget(drone_mode_title)
        
        # HI Mode indicator
        hi_mode = QWidget()
        hi_layout = QHBoxLayout(hi_mode)
        hi_layout.setContentsMargins(0, 0, 0, 0)
        hi_drone = QLabel()
        hi_drone_pixmap = QPixmap("drone.png").scaled(20, 20, Qt.KeepAspectRatio)
        hi_drone.setPixmap(hi_drone_pixmap)
        hi_drone.setStyleSheet("background-color: red; padding: 2px; border: 1px solid black;")
        hi_layout.addWidget(hi_drone)
        hi_text = QLabel("HI Mode")
        hi_layout.addWidget(hi_text)
        hi_layout.addStretch()
        drone_mode_layout.addWidget(hi_mode)
        
        # LO Mode indicator
        lo_mode = QWidget()
        lo_layout = QHBoxLayout(lo_mode)
        lo_layout.setContentsMargins(0, 0, 0, 0)
        lo_drone = QLabel()
        lo_drone_pixmap = QPixmap("drone.png").scaled(20, 20, Qt.KeepAspectRatio)
        lo_drone.setPixmap(lo_drone_pixmap)
        lo_drone.setStyleSheet("background-color: blue; padding: 2px; border: 1px solid black;")
        lo_layout.addWidget(lo_drone)
        lo_text = QLabel("LO Mode")
        lo_layout.addWidget(lo_text)
        lo_layout.addStretch()
        drone_mode_layout.addWidget(lo_mode)
        
        # Add an empty spacer widget to take up vertical space
        drone_mode_layout.addStretch()
        
        legends_layout.addWidget(drone_mode_widget)
        
        # Add the side-by-side legends container to the main layout
        layout.addWidget(legends_container)
        
        # Add a spacer at the bottom to push everything up
        layout.addStretch()
        
        layout.setSpacing(10)
        self.show()
        
    def update_energy(self, energy):
        self.energy_label.setText(f"Remaining: {int(energy)}%")
        if energy < 20:
            self.energy_label.setStyleSheet("font-size: 14px; font-weight: bold; color: red;")
        else:
            self.energy_label.setStyleSheet("font-size: 14px; font-weight: bold; color: black;")
    
    def update_mode_and_costs(self, is_hi_mode, accumulated_cost_lo, accumulated_cost_hi, consumed_energy):
        mode_text = "HI" if is_hi_mode else "LO"
        mode_color = "red" if is_hi_mode else "blue"
        self.mode_label.setText(f"Mode: {mode_text}")
        self.mode_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {mode_color};")
        self.cost_lo_label.setText(f"Acc. Cost (LO): {accumulated_cost_lo:.2f} W")
        self.cost_hi_label.setText(f"Acc. Cost (HI): {accumulated_cost_hi:.2f} W")
        self.consumed_energy_label.setText(f"Consumed Energy: {consumed_energy:.2f} W")
            
    def update_position(self, position):
        if position:
            self.x_label.setText(f"X: {position[0]:.2f}")
            self.y_label.setText(f"Y: {position[1]:.2f}")
            self.z_label.setText(f"Z: {position[2]:.2f}")