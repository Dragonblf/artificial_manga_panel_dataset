import numpy as np
import pyclipper
from ..objects.panel import Panel
from ... import config_file as cfg
from ..helpers import get_leaf_panels


def shrink_panels(page):
    """
    A function that uses the pyclipper library]
    to reduce the size of the panel polygon

    :param page: Page whose panels are to be
    shrunk

    :type page: Page

    :return: Page with shrunk panels

    :rtype: Page
    """

    panels = []
    if len(page.leaf_children) < 1:
        get_leaf_panels(page, panels)
        page.leaf_children = panels
    else:
        panels = page.leaf_children

    # For each panel
    for panel in panels:
        # Shrink them
        pco = pyclipper.PyclipperOffset()
        pco.AddPath(panel.get_polygon(),
                    pyclipper.JT_ROUND,
                    pyclipper.ET_CLOSEDPOLYGON)

        shrink_amount = np.random.randint(
            cfg.min_panel_shrink_amount, cfg.max_panel_shrink_amount)
        solution = pco.Execute(shrink_amount)

        # Get the solutions
        changed_coords = []
        if len(solution) > 0:
            for item in solution[0]:
                changed_coords.append(tuple(item))

            changed_coords.append(changed_coords[0])

            # Assign them
            panel.coords = changed_coords
            panel.x1y1 = changed_coords[0]
            panel.x2y2 = changed_coords[1]
            panel.x3y3 = changed_coords[2]
            panel.x4y4 = changed_coords[3]
        else:
            # Assign them as is if there are no solutions
            pass

    return page


def draw_n_shifted(n, parent, horizontal_vertical, shifts=[]):
    """
    A function to take a parent Panel and divide it into n
    sub-panel's vertically or horizontally with each panels having
    specified size ratios along the axis perpendicular to their orientation

    NOTE: This function performs actions by reference

    :param n: Number of sub-panels

    :type n: int

    :param parent: The parent panel being split

    :type parent: Panel

    :param horizontal_vertical: Whether to render the sub-panels vertically
    or horizontally in regards to the page

    :type horizontal_vertical: str

    :param shifts: Ratios to divide the panel into sub-panels

    :type shifts: list
    """

    # if input out of bounds i.e. 1:
    if n == 1:
        return parent

    # Specify parent panel dimensions
    topleft = parent.x1y1
    topright = parent.x2y2
    bottomright = parent.x3y3
    bottomleft = parent.x4y4

    # Allow each inital panel to grow to up to 150% of 100/n
    # which would be all panel's equal.
    # This is then normalized down to a smaller number
    choice_max = round((100/n)*1.5)
    choice_min = round((100/n)*0.5)

    normalized_shifts = []

    # If there are no ratios specified
    if len(shifts) < 1:
        shifts = []
        for i in range(0, n):
            # Randomly select a size for the new panel's side
            shift_choice = np.random.randint(choice_min, choice_max)
            # Change the maximum range acoording to available length
            # of the parent panel's size
            choice_max = choice_max + ((100/n) - shift_choice)

            # Append the shift
            shifts.append(shift_choice)

        # Amount of length to add or remove
        to_add_or_remove = (100 - sum(shifts))/len(shifts)

        # Normalize panels such that the shifts all sum to 1.0
        for shift in shifts:
            new_shift = shift + to_add_or_remove
            normalized_shifts.append(new_shift/100)
    else:
        normalized_shifts = shifts

    # If the panel is horizontal to the page
    if horizontal_vertical == "h":
        shift_level = 0.0

        # For each new panel
        for i in range(0, n):
            # If it's the first panel then it's
            # has the same left side as the parent top side
            if i == 0:
                x1y1 = topleft
                x2y2 = topright

            # If not it has the same top side as it's previous
            # sibiling's bottom side
            else:
                # this shift level is the same as the bottom side
                # of the sibling panel
                shift_level += normalized_shifts[i-1]

                # Specify points for the top side
                x1y1 = (bottomleft[0],
                        topleft[1] +
                        (bottomleft[1] - topleft[1])*shift_level)

                x2y2 = (bottomright[0],
                        topright[1] +
                        (bottomright[1] - topright[1])*shift_level)

            # If it's the last panel then it has the
            # same right side as the parent bottom side
            if i == (n-1):
                x3y3 = bottomright
                x4y4 = bottomleft

            # If not it has the same bottom side as it's next
            # sibling's top side
            else:
                # Same shift level as the left side of next sibling
                next_shift_level = shift_level + normalized_shifts[i]

                # Specify points for the bottom side
                x3y3 = (bottomright[0], topright[1] +
                        (bottomright[1] - topright[1])*next_shift_level)

                x4y4 = (bottomleft[0], topleft[1] +
                        (bottomleft[1] - topleft[1])*next_shift_level)

            # Create a Panel
            poly_coords = (x1y1, x2y2, x3y3, x4y4, x1y1)
            poly = Panel(poly_coords,
                         parent.name+"-"+str(i),
                         orientation=horizontal_vertical,
                         parent=parent,
                         children=[]
                         )

            parent.add_child(poly)

    # If the panel is vertical
    if horizontal_vertical == "v":
        shift_level = 0.0

        # For each new panel
        for i in range(0, n):

            # If it's the first panel it has the same
            # top side as the parent's left side
            if i == 0:
                x1y1 = topleft
                x4y4 = bottomleft

            # if not it's left side is the same as it's
            # previous sibling's right side
            else:
                # Same shift level as the right side of previous sibling
                shift_level += normalized_shifts[i-1]

                # Specify points for left side
                x1y1 = (topleft[0] +
                        (topright[0] - topleft[0])*shift_level,
                        topright[1])

                x4y4 = (bottomleft[0] +
                        (bottomright[0] - bottomleft[0])*shift_level,
                        bottomright[1])

            # If it's the last panel i thas the same
            # right side as it's parent panel
            if i == (n-1):
                x2y2 = topright
                x3y3 = bottomright

            # If not then it has the same right side as it's next sibling's
            # left side
            else:
                # Same shift level as next sibling's left side
                next_shift_level = shift_level + normalized_shifts[i]

                # Specify points for right side
                x2y2 = (topleft[0] +
                        (topright[0] - topleft[0])*next_shift_level,
                        topright[1])

                x3y3 = (bottomleft[0] +
                        (bottomright[0] - bottomleft[0])*next_shift_level,
                        bottomright[1])

            # Create a panel
            poly_coords = (x1y1, x2y2, x3y3, x4y4, x1y1)
            poly = Panel(poly_coords,
                         parent.name+"-"+str(i),
                         orientation=horizontal_vertical,
                         parent=parent,
                         children=[]
                         )

            parent.add_child(poly)


def draw_n(n, parent, horizontal_vertical):
    """
    A function to take a parent Panel and divide it into n
    sub-panel's vertically or horizontally with each panels having
    equal size ratios along the axis perpendicular to their orientation


    NOTE: This function performs actions by reference

    :param n: Number of sub-panels

    :type n: int

    :param parent: The parent panel being split

    :type parent: Panel

    :param horizontal_vertical: Whether to render the sub-panels vertically
    or horizontally in regards to the page

    :type horizontal_vertical: str
    """
    # if input out of bounds i.e. 1:
    if n == 1:
        return parent

    # Specify parent panel dimensions
    topleft = parent.x1y1
    topright = parent.x2y2
    bottomright = parent.x3y3
    bottomleft = parent.x4y4

    # If the panel is horizontal to the page
    if horizontal_vertical == "h":

        # For each new panel
        for i in range(0, n):

            # If it's the first panel then it's
            # has the same left side as the parent top side
            if i == 0:
                x1y1 = topleft
                x2y2 = topright
            # If not it has the same top side as it's
            # previous sibiling's bottom side
            else:

                # Specify points for the top side
                # Since it's equally divided the size is dictated by (i/n)
                x1y1 = (bottomleft[0],
                        topleft[1] + (bottomleft[1] - topleft[1])*(i/n))

                x2y2 = (bottomright[0],
                        topright[1] + (bottomright[1] - topright[1])*(i/n))

            # If it's the last panel then it has the
            # same right side as the parent bottom side
            if i == (n-1):
                x3y3 = bottomright
                x4y4 = bottomleft

            # If not it has the same bottom side as it's
            # next sibling's top side
            else:
                # Specify points for the bottom side
                # Since it's equally divided the size is dictated by (i/n)
                x3y3 = (bottomright[0],
                        topright[1] + (bottomright[1] - topright[1])*((i+1)/n))
                x4y4 = (bottomleft[0],
                        topleft[1] + (bottomleft[1] - topleft[1])*((i+1)/n))

            # Create a Panel
            poly_coords = (x1y1, x2y2, x3y3, x4y4, x1y1)
            poly = Panel(poly_coords,
                         parent.name+"-"+str(i),
                         orientation=horizontal_vertical,
                         parent=parent,
                         children=[]
                         )

            parent.add_child(poly)

    # If the panel is vertical
    if horizontal_vertical == "v":
        # For each new panel
        for i in range(0, n):

            # If it's the first panel it has the same
            # top side as the parent's left side
            if i == 0:
                x1y1 = topleft
                x4y4 = bottomleft

            # If not it's left side is the same as it's
            # previous sibling's right side
            else:
                # Specify points for left side
                # Since it's equally divided the size is dictated by (i/n)
                x1y1 = (topleft[0] +
                        (topright[0] - topleft[0])*(i/n),
                        topright[1])

                x4y4 = (bottomleft[0] +
                        (bottomright[0] - bottomleft[0])*(i/n),
                        bottomright[1])

            # If it's the last panel i thas the same
            # right side as it's parent panel
            if i == (n-1):
                x2y2 = topright
                x3y3 = bottomright

            # If not then it has the same right side as it's next sibling's
            # left side
            else:
                # Specify points for right side
                # Since it's equally divided the size is dictated by (i/n)
                x2y2 = (topleft[0] +
                        (topright[0] - topleft[0])*((i+1)/n),
                        topright[1])

                x3y3 = (bottomleft[0] +
                        (bottomright[0] - bottomleft[0])*((i+1)/n),
                        bottomright[1])

            poly_coords = (x1y1, x2y2, x3y3, x4y4, x1y1)
            poly = Panel(poly_coords,
                         parent.name+"-"+str(i),
                         orientation=horizontal_vertical,
                         parent=parent,
                         children=[]
                         )

            parent.add_child(poly)


def draw_two_shifted(parent, horizontal_vertical, shift=None):
    """
    Draw two subpanels of a parent panel

    :param parent: The parent panel to be split

    :type parent: Parent

    :param horizontal_vertical: Orientation of sub-panels in refrence
    to the page

    :type horizontal_vertical: str

    :param shift: by what ratio should the 2 panels be split, defaults to None

    :type shift: float, optional
    """

    # Specify parent panel dimensions
    topleft = parent.x1y1
    topright = parent.x2y2
    bottomright = parent.x3y3
    bottomleft = parent.x4y4

    # If shift's are not specified select them
    if shift is None:
        shift_min = 25
        shift_max = 75
        shift = np.random.randint(shift_min, shift_max)
        shift = shift/100

    # If panel is horizontal
    if horizontal_vertical == "h":

        # Spcify the first panel's coords
        r1x1y1 = topleft
        r1x2y2 = topright
        r1x3y3 = (bottomright[0],
                  topright[1] + (bottomright[1] - topright[1])*shift)
        r1x4y4 = (bottomleft[0],
                  topleft[1] + (bottomleft[1] - topleft[1])*shift)

        poly1_coords = (r1x1y1, r1x2y2, r1x3y3, r1x4y4, r1x1y1)

        # Specify the second panel's coords
        r2x1y1 = (bottomleft[0],
                  topleft[1] + (bottomleft[1] - topleft[1])*shift)
        r2x2y2 = (bottomright[0],
                  topright[1] + (bottomright[1] - topright[1])*shift)

        r2x3y3 = bottomright
        r2x4y4 = bottomleft

        poly2_coords = (r2x1y1, r2x2y2, r2x3y3, r2x4y4, r2x1y1)

        # Create panels
        poly1 = Panel(poly1_coords,
                      parent.name + "-0",
                      orientation=horizontal_vertical,
                      parent=parent,
                      children=[])

        poly2 = Panel(poly2_coords,
                      parent.name + "-1",
                      orientation=horizontal_vertical,
                      parent=parent,
                      children=[])

        parent.add_children([poly1, poly2])

    # If the panel is vertical
    if horizontal_vertical == "v":

        # Specify the first panel's coords
        r1x1y1 = topleft
        r1x2y2 = (topleft[0] + (topright[0] - topleft[0])*shift, topright[1])
        r1x3y3 = (bottomleft[0] + (bottomright[0] - bottomleft[0])*shift,
                  bottomright[1])
        r1x4y4 = bottomleft

        poly1_coords = (r1x1y1, r1x2y2, r1x3y3, r1x4y4, r1x1y1)

        # Specify the second panel's coords
        r2x1y1 = (topleft[0] + (topright[0] - topleft[0])*shift, topright[1])
        r2x2y2 = topright
        r2x3y3 = bottomright
        r2x4y4 = (bottomleft[0] + (bottomright[0] - bottomleft[0])*shift,
                  bottomright[1])

        poly2_coords = (r2x1y1, r2x2y2, r2x3y3, r2x4y4, r2x1y1)

        # Create panels
        poly1 = Panel(poly1_coords,
                      parent.name + "-0",
                      orientation=horizontal_vertical,
                      parent=parent,
                      children=[])

        poly2 = Panel(poly2_coords,
                      parent.name + "-1",
                      orientation=horizontal_vertical,
                      parent=parent,
                      children=[])

        parent.add_children([poly1, poly2])
