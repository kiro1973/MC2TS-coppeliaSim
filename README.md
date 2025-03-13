# Drone Simulation with Energy and Wind Effect

This project simulates the movement of a drone between predefined points while accounting for energy consumption and wind effects on specific areas (circular).

## Features
- Simulates drone movement between various sensors to collect data .
- Calculates energy consumption for each move.
- Adds wind effects to certain areas , influencing the drone's performance.

## Setup Instructions
1. go to the `my_NodeImplementation_2.py` --> this file and the MCTS contain the algortihm controlling the drone 
2. and in the line `controller.run_algorithm(do_drone_navigation)` in the main you can change the method used for drone navigation by another one you prefer but have a look first of how it functions
3. the main 2 functions called in the function `do_drone_navigation` to interact with the drone simulation module is the `move_drone_to_sensor` and `get_consumed_energy`

## Usage
1. You can define your own parameters in the config file like 
    ```python
    points = {
        "B": {"x": 5, "y": 7},
        "C1": {"x": 1, "y": 5, "c": True},
        "C2": {"x": 2, "y": 1, "c": False},
        "C3": {"x": 6, "y": 2, "c": True},
        "C4": {"x": 10, "y": 6, "c": False},
    }
    ```

2. or Specify the moves and areas where wind effects will be present:
    ```python
    # Here we are pretending the areas of wind exist during all the moves. You can define yours.
    wind_regions = [
        {'center': (2, 3), 'radius': 3.0, 'moves': [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]},
        {'center': (8, 7), 'radius': 2.5, 'moves': [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]}
    ]
    ```

3. In your controller you instantiate an object from the class  `DroneSimulation` class with the defined parameters:
    ```python
    simulation = DroneSimulation(points, wind_moves)
    ```
    and pass it to the drone navigation function

4. in the algorithm of navigation in our case found Use the additional function `get_consumed_energy` to retrieve the energy details for the simulation:
    ```python
    energy_consumed = simulation.get_consumed_energy()
    print(f"Total energy consumed: {energy_consumed}")
    ```

