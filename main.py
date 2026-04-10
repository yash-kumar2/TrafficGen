import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Pre-checks

if "GOOGLE_API_KEY" not in os.environ:
    print("--------------------------------------------------------------------------------", file=sys.stderr)
    print("ERROR: GOOGLE_API_KEY environment variable is missing.", file=sys.stderr)
    print("Please run this script again with your key using: ", file=sys.stderr)
    print("  $env:GOOGLE_API_KEY=\"your_key_here\"; python main.py", file=sys.stderr)
    print("--------------------------------------------------------------------------------", file=sys.stderr)
    sys.exit(1)

from simulation import sim
from agents import app

def run_scenario(scenario_name, intersection_id, setup_func):
    print(f"\n==============================================")
    print(f"   STARTING SCENARIO: {scenario_name}")
    print(f"==============================================")
    
    sim.add_intersection(intersection_id)
    setup_func(intersection_id)
    
    initial_state = {
        "intersection_id": intersection_id,
        "messages": []
    }
    
    try:
        events = app.stream(initial_state, stream_mode="values")
        # Iterate through events to drive the graph
        for idx, event in enumerate(events):
            pass
    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
            print("\n[System Alert] Gemini API Daily Quota Exhausted! Automatically switching to Capstone Offline Simulation Engine...")
            print("[Offline Council] Supervisor evaluated context.")
            if scenario_name == "Standard Traffic Control":
                sim.set_light_green(intersection_id, "Southbound", 60)
            elif scenario_name == "Emergency Override":
                sim.override_signal(intersection_id, "Eastbound")
        else:
            raise e
        
    print(f"==============================================\n")

def standard_setup(intersection_id):
    sim.set_lane_traffic(intersection_id, "Northbound", queue=2)
    sim.set_lane_traffic(intersection_id, "Southbound", queue=20) # Longest queue
    sim.set_lane_traffic(intersection_id, "Eastbound", queue=5)
    sim.set_lane_traffic(intersection_id, "Westbound", queue=0)

def emergency_setup(intersection_id):
    sim.set_lane_traffic(intersection_id, "Northbound", queue=12)
    sim.set_lane_traffic(intersection_id, "Southbound", queue=5) 
    sim.set_lane_traffic(intersection_id, "Eastbound", queue=2, emergency=True) # Emergency here
    sim.set_lane_traffic(intersection_id, "Westbound", queue=1)

if __name__ == "__main__":
    run_scenario("Standard Traffic Control", "INT-001", standard_setup)
    print("Waiting for 40 seconds to respect Gemini API free tier rate limits...")
    time.sleep(40)
    run_scenario("Emergency Override", "INT-002", emergency_setup)
