import json, dash

app = dash.Dash(__name__)

# To parse the json
def load_layout_from_json(filepath):
    with open(filepath, "r", encoding="UTF-8") as f:
        layout_dict = json.load(f)
    return parse_component(layout_dict)

def parse_component(component_dict):
    if isinstance(component_dict, dict):
        if "type" in component_dict and "namespace" in component_dict:
            # Recreate Dash component
            component_type = getattr(dash.dcc if component_dict["namespace"] == "dash_core_components" else dash.html, component_dict["type"])
            props = {k: parse_component(v) for k, v in component_dict.get("props", {}).items()}
            return component_type(**props)
        else:
            # Recursively parse nested dictionaries
            return {k: parse_component(v) for k, v in component_dict.items()}
    elif isinstance(component_dict, list):
        # Recursively parse lists
        return [parse_component(item) for item in component_dict]
    else:
        # Base case: return the value as-is
        return component_dict

loaded_layout = load_layout_from_json("layout.json")

app.layout = loaded_layout

server = app.server