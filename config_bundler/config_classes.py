

import datetime
from enum import Enum
from pydantic import BaseModel, Field, schema_json_of

"""
######################## cross-type-classes ########################
"""
class DisplayType(str, Enum):
    """
    There is a concept of 'how to interact with the board'.
    overlay: cover up the idle screen, but not indicators - e.g. muted, on-the-air
    idle: the 'always on' screen, e.g date, time, indicators, etc
    """
    overlay     = "overlay"
    momentary   = "momentary"
    idle        = "idle"

class Timestamp(float):
    """
    e.g. time.time() -> 1667128398.6528692
    """
    timestamp = float

class Function(str, Enum):
    """
    This is used for function-encompassing logic decisions.
    """
    zoom = "zoom"
    network = "network"

"""
######################## per-type-classes ########################
"""

class ZoomState(str, Enum):
    muted       = "muted"
    unmuted     = "unmuted"
    inactive    = "inactive"

class NetworkIndicatorColour(str, Enum):
    green       = "green"
    yellow      = "yellow"
    red         = "red"



"""
######################## assembled-classes ########################
"""

class ZoomConfigModel(BaseModel):
    """
    The zoom functionality's config description.
    """
    zoom_state : ZoomState
    display_type : DisplayType
    timestamp : Timestamp

class NetworkConfigModel(BaseModel):
    """
    The network indicator functionality's config description.
    """
    indicator_colour : NetworkIndicatorColour
    display_type : DisplayType
    timestamp : Timestamp

"""
######################## bundled-and-returned-class ########################
"""

class BundledConfigModel(BaseModel):
    """
        We want to build an object that allows us to inject in config components
        and returns the built config.
    """
    network_config : NetworkConfigModel
    zoom_config : ZoomConfigModel

