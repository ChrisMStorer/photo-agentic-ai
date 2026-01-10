
import asyncio
from mcp import Tool
from mcp.server import Server
import mcp.server.stdio
import exifread
from geopy.geocoders import Nominatim
server = Server("photo-agent")

@server.call_tool()
def get_location_name_from_gps_coords(latitude: float, longitude: float) -> str:
    """Get location name from GPS coordinates using Nominatim API"""
    breakpoint
    geolocator = Nominatim(user_agent="note_taking_agent")
    location = geolocator.reverse((latitude, longitude), exactly_one=True)
    if location:
        return f"Location name for coordinates ({latitude}, {longitude}): {location.address}"
    else:
        return f"Could not find location for coordinates ({latitude}, {longitude})"

@server.call_tool()
def get_image_location_metadata(filepath: str) -> str:
    """Get image location metadata from a file using ExifRead"""
    breakpoint
    try:
        with open(filepath, 'rb') as f:
            tags = exifread.process_file(f)
        gps_latitude = tags.get('GPS GPSLatitude')
        gps_longitude = tags.get('GPS GPSLongitude')
        if gps_latitude and gps_longitude:
            return f"Image location metadata for {filepath}:\nLatitude: {gps_latitude}\nLongitude: {gps_longitude}"
        else:
            return f"No GPS metadata found in {filepath}."
    except FileNotFoundError:
        return f"Error: The file {filepath} was not found."
    except Exception as e:
        return f"An error occurred while reading metadata from {filepath}: {str(e)}"

if __name__ == "__main__":
    mcp.server.stdio.run_server(server)