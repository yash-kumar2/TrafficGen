from simulation import sim
from typing import Dict, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field

class PerceptionModule:
    @staticmethod
    def telemetry_to_text(telemetry: Dict[str, Any]) -> str:
        """
        Translates raw telemetry into semantic context strings.
        """
        if not telemetry:
            return "No data for intersection."
            
        inter_id = telemetry["id"]
        lanes = telemetry["lanes"]
        
        description = []
        emergency_detected = False
        
        for lane_name, lane_data in lanes.items():
            queue = lane_data["queue"]
            wait_time = lane_data.get("wait_time_s", 0)
            is_emergency = lane_data["emergency_vehicle"]
            
            status = "clear"
            if queue > 15:
                status = "heavy congestion"
            elif queue > 5:
                status = "moderate traffic"
            elif queue > 0:
                status = "light traffic"
                
            lane_desc = f"- {lane_name}: {status} ({queue} vehicles in queue, longest wait: {wait_time}s)"
            if is_emergency:
                lane_desc += " [EMERGENCY VEHICLE DETECTED]"
                emergency_detected = True
                
            description.append(lane_desc)
            
        context = f"Telemetry snapshot for Intersection '{inter_id}':\n" + "\n".join(description)
        if emergency_detected:
            context = "CRITICAL SITUATION: Emergency vehicle approaching!\n" + context
            
        return context

# Action Tools
class LightGreenInput(BaseModel):
    intersection_id: str = Field(description="ID of the intersection")
    lane: str = Field(description="Lane to set to green, e.g., Northbound, Southbound")
    duration_seconds: int = Field(description="How long to keep light green in seconds")

@tool("set_light_green", args_schema=LightGreenInput)
def set_light_green(intersection_id: str, lane: str, duration_seconds: int) -> str:
    """Set the traffic light to green for a specific lane and duration."""
    success = sim.set_light_green(intersection_id, lane, duration_seconds)
    if success:
        return f"Successfully set light to GREEN for {lane} at {intersection_id} for {duration_seconds}s."
    return f"Failed to set light. Intersection {intersection_id} not found."

class OverrideSignalInput(BaseModel):
    intersection_id: str = Field(description="ID of the intersection")
    lane: str = Field(description="Lane with the emergency vehicle to set to green immediately")

@tool("override_signal", args_schema=OverrideSignalInput)
def override_signal(intersection_id: str, lane: str) -> str:
    """Immediately override the traffic light to green for an emergency vehicle."""
    success = sim.override_signal(intersection_id, lane)
    if success:
        return f"Successfully executed emergency OVERRIDE for {lane} at {intersection_id}."
    return f"Failed to execute override. Intersection {intersection_id} not found."

action_tools = [set_light_green, override_signal]
