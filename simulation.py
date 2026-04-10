class MockTrafficSimulation:
    def __init__(self):
        self.intersections = {}

    def add_intersection(self, intersection_id):
        self.intersections[intersection_id] = {
            "id": intersection_id,
            "lanes": {
                "Northbound": {"queue": 0, "wait_time_s": 0, "emergency_vehicle": False},
                "Southbound": {"queue": 0, "wait_time_s": 0, "emergency_vehicle": False},
                "Eastbound": {"queue": 0, "wait_time_s": 0, "emergency_vehicle": False},
                "Westbound": {"queue": 0, "wait_time_s": 0, "emergency_vehicle": False},
            },
            "light_state": "Red", 
            "active_green_lane": "Northbound",
            "awaiting_vehicles": 0,
            "total_wait_time_metric": 0
        }

    def set_lane_traffic(self, intersection_id, lane, queue, wait_time=0, emergency=False):
        if intersection_id in self.intersections and lane in self.intersections[intersection_id]["lanes"]:
            self.intersections[intersection_id]["lanes"][lane]["queue"] = queue
            self.intersections[intersection_id]["lanes"][lane]["wait_time_s"] = wait_time
            self.intersections[intersection_id]["lanes"][lane]["emergency_vehicle"] = emergency

    def get_sensors_data(self, intersection_id):
        if intersection_id not in self.intersections:
            return None
        return self.intersections[intersection_id]

    def set_light_green(self, intersection_id, lane, duration_seconds: int):
        if intersection_id in self.intersections:
            self.intersections[intersection_id]["light_state"] = "Green"
            self.intersections[intersection_id]["active_green_lane"] = lane
            print(f"[SIMULATION] Intersection '{intersection_id}': Light set to GREEN for {lane} ({duration_seconds}s).")
            # Clear queue and wait time for this lane
            self.intersections[intersection_id]["lanes"][lane]["queue"] = 0
            self.intersections[intersection_id]["lanes"][lane]["wait_time_s"] = 0
            self.intersections[intersection_id]["lanes"][lane]["emergency_vehicle"] = False
            return True
        return False

    def override_signal(self, intersection_id, lane):
        if intersection_id in self.intersections:
            self.intersections[intersection_id]["light_state"] = "Green"
            self.intersections[intersection_id]["active_green_lane"] = lane
            print(f"[SIMULATION] EMERGENCY OVERRIDE! Intersection '{intersection_id}' Light set to GREEN for {lane}.")
            self.intersections[intersection_id]["lanes"][lane]["queue"] = 0
            self.intersections[intersection_id]["lanes"][lane]["wait_time_s"] = 0
            self.intersections[intersection_id]["lanes"][lane]["emergency_vehicle"] = False
            return True
        return False

class RuleBasedController:
    """ Rigid baseline controller that just does simple Round-Robin or static assignment. """
    def __init__(self):
        self.lane_order = ["Northbound", "Southbound", "Eastbound", "Westbound"]
        self.current_idx = 0
        
    def act(self, intersection_id, sim_instance):
        lane = self.lane_order[self.current_idx]
        self.current_idx = (self.current_idx + 1) % len(self.lane_order)
        # Rigidly assigns 60s to next lane in round robin
        print(f"[RULE-BASED] Controller blindly cycling to next phase.")
        sim_instance.set_light_green(intersection_id, lane, 60)
        return lane

# Global instance for our tools to interact with
sim = MockTrafficSimulation()
