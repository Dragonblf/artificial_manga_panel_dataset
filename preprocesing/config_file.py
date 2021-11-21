# **Page rendering**
page_width = 1600
page_height = 2400

page_size = (page_width, page_height)

output_format = ".png"
metadata_format = ".json"

boundary_width = 16

# **Font coverage**
# How many characters of the dataset should the font files support
font_character_coverage = 0.76


# **Panel Drawing**
# *Panel ratios*

# TODO: Figure out page type distributions
num_pages_ratios = {
    1: 0.125,
    2: 0.125,
    3: 0.125,
    4: 0.125,
    5: 0.125,
    6: 0.125,
    7: 0.125,
    8: 0.125
}

vertical_horizontal_ratios = {
    "v": 0.1,
    "h": 0.1,
    "vh": 0.8
}

# Panel transform chance
panel_transform_chance = 0.96

# Panel shrinking
min_panel_shrink_amount = -24
max_panel_shrink_amount = -0

# Panel removal
panel_removal_chance = 0.012
panel_removal_max = 2

# Background adding
background_add_chance = 0.012

# **Speech bubbles**
min_speech_bubbles_per_panel = 1
max_speech_bubbles_per_panel = 2

bubble_content_padding = 24
bubble_to_panel_area_max_ratio = 0.48
bubble_mask_x_increase = 16
bubble_mask_y_increase = 16
min_font_size = 24
max_font_size = 48

# *Transformations*

# Slicing
double_slice_chance = 0.24
slice_minimum_panel_area = 0.24
center_side_ratio = 0.72

# Box transforms
box_transform_panel_chance = 0.16
panel_box_trapezoid_ratio = 0.48

# How much at most should the trapezoid/rhombus start from
# as a ratio of the smallest panel's width or height
trapezoid_movement_limit = 48
rhombus_movement_limit = 48

full_page_movement_proportion_limit = 24
