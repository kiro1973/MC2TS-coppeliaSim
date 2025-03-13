import threading
import time
import math
from coppeliasim_zmqremoteapi_client import RemoteAPIClient
class DroneMonitor(threading.Thread):
    def __init__(self, simulation, window):
        super().__init__()
        self.simulation = simulation
        self.window = window
        self.running = True
        self.client = RemoteAPIClient()
        self.sim = self.client.getObject('sim')
        self.daemon = True  # Ensures thread exits when main program exits

    def run(self):
        while self.running:
            try:
                energy = self.simulation.get_remaining_energy()
                energy=math.ceil(energy)
                
                self.window.update_energy(energy)
                
                if hasattr(self.simulation, 'is_hi_mode'):
                    self.window.update_mode_and_costs(
                        self.simulation.is_hi_mode, 
                        self.simulation.accumulated_cost_mode_LO, 
                        self.simulation.accumulated_cost_mode_HI, 
                        self.simulation.consumed_energy
                    )
                
                if self.simulation.quadcopter_handle is not None:
                    position = self.sim.getObjectPosition(self.simulation.quadcopter_handle, -1)
                    self.window.update_position(position)
                
                time.sleep(0.1)  # Reduce CPU usage
            except Exception as e:
                print(f"Error in monitor thread: {e}")
                break

    def stop(self):
        self.running = False