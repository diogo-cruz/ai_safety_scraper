import json
import math
import os

def split_json_file(input_file, num_parts=5):
    # Read the JSON file
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Find the largest array in the JSON structure
    def find_largest_array(obj, current_max=None):
        if isinstance(obj, list):
            if current_max is None or len(obj) > len(current_max):
                current_max = obj
        elif isinstance(obj, dict):
            for value in obj.values():
                current_max = find_largest_array(value, current_max)
        return current_max
    
    largest_array = find_largest_array(data)
    if largest_array is None:
        raise ValueError("No array found in the JSON structure to split")
    
    # Calculate items per part
    total_items = len(largest_array)
    items_per_part = math.ceil(total_items / num_parts)
    
    # Create a deep copy of the data structure for each part
    def replace_array_in_structure(obj, new_array):
        if isinstance(obj, list) and obj is largest_array:
            return new_array
        elif isinstance(obj, dict):
            return {k: replace_array_in_structure(v, new_array) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_array_in_structure(item, new_array) for item in obj]
        return obj
    
    # Split and save parts
    for i in range(num_parts):
        start_idx = i * items_per_part
        end_idx = min((i + 1) * items_per_part, total_items)
        
        # Skip if no items left
        if start_idx >= total_items:
            break
        
        # Get the slice of the largest array
        part_array = largest_array[start_idx:end_idx]
        
        # Create a new structure with the partial array
        part_data = replace_array_in_structure(data, part_array)
        
        # Generate output filename
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_part{i+1}.json"
        
        # Save the part
        with open(output_file, 'w') as f:
            json.dump(part_data, f, indent=2)
        
        print(f"Created {output_file} with {len(part_array)} items in the main array")

if __name__ == "__main__":
    input_file = "www_lakera_ai_data.json"
    try:
        split_json_file(input_file)
        print("Successfully split the JSON file into parts")
    except Exception as e:
        print(f"Error: {str(e)}") 