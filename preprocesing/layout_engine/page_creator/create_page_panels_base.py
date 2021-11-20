
import numpy as np

from ... import config_file as cfg
from ..objects.page import Page
from .create_speech_bubbles_metadata import *
from .page_panels_shifters import *
from ..helpers import invert_for_next, choose, choose_and_return_other


def create_page_panels_base(num_panels=0,
                            layout_type=None,
                            type_choice=None,
                            page_name=None):
    """
    This function creates the base panels for one page
    it specifies how a page should be layed out and
    how many panels should be in it

    :param num_panels: how many panels should be on a page
    if 0 then the function chooses, defaults to 0

    :type num_panels: int, optional

    :param layout_type: whether the page should consist of
    vertical, horizontal or both types of panels, defaults to None

    :type layout_type: str, optional

    :param type_choice: If having selected vh panels select a type
    of layout specifically, defaults to None

    :type type_choice: str, optional

    :param page_name: A specific name for the page

    :type page_name: str, optional

    :return: A Page object with the panels initalized

    :rtype: Page
    """

    # TODO: Skew panel number distribution

    # Page dimensions turned to coordinates
    topleft = (0.0, 0.0)
    topright = (cfg.page_width, 0.0)
    bottomleft = (0.0, cfg.page_height)
    bottomright = cfg.page_size
    coords = [
        topleft,
        topright,
        bottomright,
        bottomleft
    ]

    if layout_type is None:
        layout_type = np.random.choice(["v", "h", "vh"])

    # Panels encapsulated and returned within page
    if page_name is None:
        page = Page(coords, layout_type, num_panels)
    else:
        page = Page(coords, layout_type, num_panels, name=page_name)

    # If you want only vertical panels
    if layout_type == "v":
        max_num_panels = 4
        if num_panels < 1:
            num_panels = np.random.choice([3, 4])
            page.num_panels = num_panels
        else:
            page.num_panels = num_panels

        draw_n_shifted(num_panels, page, "v")

    # If you want only horizontal panels
    elif layout_type == "h":
        max_num_panels = 5
        if num_panels < 1:
            num_panels = np.random.randint(3, max_num_panels+1)
            page.num_panels = num_panels
        else:
            page.num_panels = num_panels

        draw_n_shifted(num_panels, page, "h")

    # If you want both horizontal and vertical panels
    elif layout_type == "vh":
        max_num_panels = 8
        if num_panels < 1:
            num_panels = np.random.randint(2, max_num_panels+1)
            page.num_panels = num_panels
        else:
            page.num_panels = num_panels

        if num_panels == 2:
            # Draw 2 rectangles
            # vertically or horizontally
            horizontal_vertical = np.random.choice(["h", "v"])
            draw_two_shifted(page, horizontal_vertical)

        if num_panels == 3:
            # Draw 2 rectangles
            # Vertically or Horizontally

            horizontal_vertical = np.random.choice(["h", "v"])
            draw_two_shifted(page, horizontal_vertical)

            next_div = invert_for_next(horizontal_vertical)

            # Pick one and divide it into 2 rectangles
            choice_idx = choose(page)
            choice = page.get_child(choice_idx)

            draw_two_shifted(choice, next_div)

        if num_panels == 4:
            horizontal_vertical = np.random.choice(["h", "v"])

            # Possible layouts with 4 panels
            if type_choice is None:
                type_choice = np.random.choice(["eq", "uneq", "div",
                                                "trip", "twoonethree"])

            # Draw two rectangles
            if type_choice == "eq":
                draw_two_shifted(page, horizontal_vertical, shift=0.5)
                next_div = invert_for_next(horizontal_vertical)

                # Divide each into 2 rectangles equally
                shift_min = 25
                shift_max = 75
                shift = np.random.randint(shift_min, shift_max)
                shift = shift/100

                draw_two_shifted(page.get_child(0), next_div, shift)
                draw_two_shifted(page.get_child(1), next_div, shift)

            # Draw two rectangles
            elif type_choice == "uneq":
                draw_two_shifted(page, horizontal_vertical, shift=0.5)
                next_div = invert_for_next(horizontal_vertical)

                # Divide each into 2 rectangles unequally
                draw_two_shifted(page.get_child(0), next_div)
                draw_two_shifted(page.get_child(1), next_div)

            elif type_choice == "div":
                draw_two_shifted(page, horizontal_vertical, shift=0.5)
                next_div = invert_for_next(horizontal_vertical)

                # Pick one and divide into 2 rectangles
                choice1_idx = choose(page)
                choice1 = page.get_child(choice1_idx)

                draw_two_shifted(choice1, next_div)

                # Pick one of these two and divide that into 2 rectangles
                choice2_idx = choose(choice1)
                choice2 = choice1.get_child(choice2_idx)

                next_div = invert_for_next(next_div)
                draw_two_shifted(choice2, next_div)

            # Draw three rectangles
            elif type_choice == "trip":
                draw_n(3, page, horizontal_vertical)

                # Pick one and divide it into two
                choice_idx = choose(page)
                choice = page.get_child(choice_idx)

                next_div = invert_for_next(horizontal_vertical)

                draw_two_shifted(choice, next_div)

            # Draw two rectangles
            elif type_choice == "twoonethree":

                draw_two_shifted(page, horizontal_vertical)

                # Pick one and divide it into 3 rectangles
                choice_idx = choose(page)
                choice = page.get_child(choice_idx)

                next_div = invert_for_next(horizontal_vertical)

                draw_n_shifted(3, choice, next_div)

        if num_panels == 5:

            # Draw two rectangles
            horizontal_vertical = np.random.choice(["h", "v"])

            # Possible layouts with 5 panels
            if type_choice is None:
                type_choice = np.random.choice(["eq", "uneq", "div",
                                                "twotwothree", "threetwotwo",
                                                "fourtwoone"])

            if type_choice == "eq" or type_choice == "uneq":

                draw_two_shifted(page, horizontal_vertical, shift=0.5)
                next_div = invert_for_next(horizontal_vertical)

                # Pick one and divide it into two then
                choice_idx = choose(page)
                choice = page.get_child(choice_idx)

                draw_two_shifted(choice, next_div)

                # Divide each into 2 rectangles equally
                if type_choice == "eq":
                    shift_min = 25
                    shift_max = 75
                    shift = np.random.randint(shift_min, shift_max)
                    set_shift = shift / 100
                else:
                    # Divide each into 2 rectangles unequally
                    set_shift = None

                next_div = invert_for_next(next_div)
                draw_two_shifted(choice.get_child(0),
                                 next_div,
                                 shift=set_shift)

                draw_two_shifted(choice.get_child(1),
                                 next_div,
                                 shift=set_shift)

            # Draw two rectangles
            elif type_choice == "div":
                draw_two_shifted(page, horizontal_vertical, shift=0.5)
                next_div = invert_for_next(horizontal_vertical)

                # Divide both equally
                draw_two_shifted(page.get_child(0), next_div)
                draw_two_shifted(page.get_child(1), next_div)

                # Pick one of all of them and divide into two
                page_child_chosen = np.random.choice(page.children) 
                choice_idx, left_choices = choose_and_return_other(
                    page_child_chosen
                )

                choice = page_child_chosen.get_child(choice_idx)

                next_div = invert_for_next(next_div)
                draw_two_shifted(choice,
                                 horizontal_vertical=next_div,
                                 shift=0.5
                                 )

            # Draw two rectangles
            elif type_choice == "twotwothree":

                draw_two_shifted(page, horizontal_vertical, shift=0.5)
                next_div = invert_for_next(horizontal_vertical)

                # Pick which one gets 2 and which gets 3
                choice_idx, left_choices = choose_and_return_other(page)
                choice = page.get_child(choice_idx)
                other = page.get_child(left_choices[0])

                # Divide one into 2
                next_div = invert_for_next(horizontal_vertical)
                draw_two_shifted(choice, next_div)

                # Divide other into 3
                draw_n(3, other, next_div)

            # Draw 3 rectangles (horizontally or vertically)
            elif type_choice == "threetwotwo":

                draw_n(3, page, horizontal_vertical)
                next_div = invert_for_next(horizontal_vertical)

                choice1_idx, left_choices = choose_and_return_other(page)
                choice2_idx = np.random.choice(left_choices)
                choice1 = page.get_child(choice1_idx)
                choice2 = page.get_child(choice2_idx)

                # Pick two and divide each into two
                draw_two_shifted(choice1, next_div)
                draw_two_shifted(choice2, next_div)

            # Draw 4 rectangles vertically
            elif type_choice == "fourtwoone":
                draw_n(4, page, horizontal_vertical)

                # Pick one and divide into two
                choice_idx = choose(page)
                choice = page.get_child(choice_idx)

                next_div = invert_for_next(horizontal_vertical)
                draw_two_shifted(choice, next_div)

        if num_panels == 6:

            # Possible layouts with 6 panels
            if type_choice is None:
                type_choice = np.random.choice(["tripeq", "tripuneq",
                                                "twofourtwo", "twothreethree",
                                                "fourtwotwo"])

            horizontal_vertical = np.random.choice(["v", "h"])

            # Draw 3 rectangles (V OR H)
            if type_choice == "tripeq" or type_choice == "tripuneq":
                draw_n_shifted(3, page, horizontal_vertical)
                # Split each equally
                if type_choice == "tripeq":
                    shift = np.random.randint(25, 75)
                    shift = shift/100
                # Split each unequally
                else:
                    shift = None

                next_div = invert_for_next(horizontal_vertical)
                for panel in page.children:
                    draw_two_shifted(panel, next_div, shift=shift)

            # Draw 2 rectangles
            elif type_choice == "twofourtwo":
                draw_two_shifted(page, horizontal_vertical)
                # Split into 4 one half 2 in another
                next_div = invert_for_next(horizontal_vertical)
                draw_n_shifted(4, page.get_child(0), next_div)
                draw_two_shifted(page.get_child(1), next_div)

            # Draw 2 rectangles
            elif type_choice == "twothreethree":
                # Split 3 in each
                draw_two_shifted(page, horizontal_vertical)
                next_div = invert_for_next(horizontal_vertical)

                for panel in page.children:
                    # Allow each inital panel to grow to up to 75% of 100/n
                    n = 3
                    shifts = []
                    choice_max = round((100/n)*1.5)
                    choice_min = round((100/n)*0.5)
                    for i in range(0, n):
                        shift_choice = np.random.randint(
                            choice_min,
                            choice_max
                        )

                        choice_max = choice_max + ((100/n) - shift_choice)
                        shifts.append(shift_choice)

                    to_add_or_remove = (100 - sum(shifts))/len(shifts)

                    normalized_shifts = []
                    for shift in shifts:
                        new_shift = shift + to_add_or_remove
                        normalized_shifts.append(new_shift/100)

                    draw_n_shifted(3,
                                   panel,
                                   next_div,
                                   shifts=normalized_shifts
                                   )

            # Draw 4 rectangles
            elif type_choice == "fourtwotwo":
                draw_n_shifted(4, page, horizontal_vertical)

                # Split two of them
                choice1_idx, left_choices = choose_and_return_other(page)
                choice2_idx = np.random.choice(left_choices)
                choice1 = page.get_child(choice1_idx)
                choice2 = page.get_child(choice2_idx)

                next_div = invert_for_next(horizontal_vertical)
                draw_two_shifted(choice1, next_div)
                draw_two_shifted(choice2, next_div)

        if num_panels == 7:

            # Possible layouts with 7 panels
            types = ["twothreefour", "threethreetwotwo", "threefourtwoone",
                     "threethreextwoone", "fourthreextwo"]

            if type_choice is None:
                type_choice = np.random.choice(types)

            # Draw two split 3-4 - HV
            # Draw two rectangles
            if type_choice == "twothreefour":
                horizontal_vertical = np.random.choice(["h", "v"])

                draw_two_shifted(page, horizontal_vertical, shift=0.5)

                # Pick one and split one into 4 rectangles
                choice_idx, left_choices = choose_and_return_other(page)
                choice = page.get_child(choice_idx)
                other = page.get_child(left_choices[0])

                next_div = invert_for_next(horizontal_vertical)

                draw_n_shifted(4, choice, next_div)

                # Some issue with the function calls and seeding
                n = 3
                shifts = []
                choice_max = round((100/n)*1.5)
                choice_min = round((100/n)*0.5)
                for i in range(0, n):
                    shift_choice = np.random.randint(choice_min, choice_max)
                    choice_max = choice_max + ((100/n) - shift_choice)
                    shifts.append(shift_choice)

                to_add_or_remove = (100 - sum(shifts))/len(shifts)

                normalized_shifts = []
                for shift in shifts:
                    new_shift = shift + to_add_or_remove
                    normalized_shifts.append(new_shift/100)

                # Pick another and split into 3 rectangles
                draw_n_shifted(3, other, next_div, shifts=normalized_shifts)

            # Draw three rectangles
            elif type_choice == "threethreetwotwo":
                draw_n(3, page, "h")

                # Pick one and split it into 3 rectangles
                choice_idx, left_choices = choose_and_return_other(page)
                choice = page.get_child(choice_idx)

                draw_n_shifted(3, choice, "v")

                # Split the other two into 2 rectangles
                draw_two_shifted(page.get_child(left_choices[0]), "v")
                draw_two_shifted(page.get_child(left_choices[1]), "v")

            # Draw 3 rectangles
            elif type_choice == "threefourtwoone":
                draw_n(3, page, "h")

                # Pick two of three rectangles and let one be
                choice_idx, left_choices = choose_and_return_other(page)
                choice = page.get_child(choice_idx)
                other_idx = np.random.choice(left_choices)
                other = page.get_child(other_idx)

                # Of the picked split one into 4 rectangles
                draw_n_shifted(4, choice, "v")

                # Split the other into 2 rectangles
                draw_two_shifted(other, "v")

            # Draw 3 rectangles
            elif type_choice == "threethreextwoone":

                draw_n(3, page, "h")

                # Pick two and leave one
                choice_idx, left_choices = choose_and_return_other(page)
                choice = page.get_child(choice_idx)
                other = page.get_child(left_choices[0])

                # Of the picked split one into 3
                draw_n_shifted(3, choice, "v")

                # Some issue with the function calls and seeding
                n = 3
                shifts = []
                choice_max = round((100/n)*1.5)
                choice_min = round((100/n)*0.5)
                for i in range(0, n):
                    shift_choice = np.random.randint(choice_min, choice_max)
                    choice_max = choice_max + ((100/n) - shift_choice)
                    shifts.append(shift_choice)

                to_add_or_remove = (100 - sum(shifts))/len(shifts)

                normalized_shifts = []
                for shift in shifts:
                    new_shift = shift + to_add_or_remove
                    normalized_shifts.append(new_shift/100)

                # Split the other into 3 as well
                draw_n_shifted(3, other, "v", shifts=normalized_shifts)

            # Draw 4 split 3x2 - HV

            # Draw 4 rectangles
            elif type_choice == "fourthreextwo":
                horizontal_vertical = np.random.choice(["h", "v"])
                draw_n(4, page, horizontal_vertical)

                # Choose one and leave as is
                choice_idx, left_choices = choose_and_return_other(page)

                # Divide the rest into two
                next_div = invert_for_next(horizontal_vertical)
                for panel in left_choices:
                    draw_two_shifted(page.get_child(panel), next_div)

        if num_panels == 8:

            # Possible layouts for 8 panels
            types = ["fourfourxtwoeq", "fourfourxtwouneq",
                     "threethreethreetwo", "threefourtwotwo",
                     "threethreefourone"]

            if type_choice is None:
                type_choice = np.random.choice(types)

            # Draw 4 rectangles
            # equal or uneqal 4-4x2
            if type_choice == types[0] or type_choice == types[1]:
                # panels = draw_n_shifted(4, *coords, "h")
                draw_n(4, page, "h")
                # Equal
                if type_choice == "fourfourxtwoeq":
                    shift_min = 25
                    shift_max = 75
                    shift = np.random.randint(shift_min, shift_max)
                    set_shift = shift/100
                # Unequal
                else:
                    set_shift = None

                # Drivide each into two
                for panel in page.children:

                    draw_two_shifted(panel, "v", shift=set_shift)

            # Where three rectangles need to be drawn
            if type_choice in types[2:]:
                draw_n(3, page, "h")

                # Draw 3 rectangles then
                if type_choice == "threethreethreetwo":

                    # Choose one and divide it into two
                    choice_idx, left_choices = choose_and_return_other(page)
                    choice = page.get_child(choice_idx)
                    draw_two_shifted(choice, "v")

                    # Divide the rest into 3
                    for panel in left_choices:
                        # Some issue with the function calls and seeding
                        n = 3
                        shifts = []
                        choice_max = round((100/n)*1.5)
                        choice_min = round((100/n)*0.5)
                        for i in range(0, n):
                            shift_choice = np.random.randint(
                                choice_min,
                                choice_max
                            )

                            choice_max = choice_max + ((100/n) - shift_choice)
                            shifts.append(shift_choice)

                        to_add_or_remove = (100 - sum(shifts))/len(shifts)

                        normalized_shifts = []
                        for shift in shifts:
                            new_shift = shift + to_add_or_remove
                            normalized_shifts.append(new_shift/100)

                        draw_n_shifted(3,
                                       page.get_child(panel),
                                       "v",
                                       shifts=normalized_shifts
                                       )

                # Draw 3 rectangles then
                elif type_choice == "threefourtwotwo":

                    # Choosen one and divide it into 4
                    choice_idx, left_choices = choose_and_return_other(page)
                    choice = page.get_child(choice_idx)

                    draw_n_shifted(4, choice, "v")

                    for panel in left_choices:
                        draw_two_shifted(page.get_child(panel), "v")

                # Draw 3 3-4-1 - H

                # Draw three rectangles then
                elif type_choice == "threethreefourone":

                    # Choose two and leave one as is
                    choice_idx, left_choices = choose_and_return_other(page)
                    choice = page.get_child(choice_idx)
                    other_idx = np.random.choice(left_choices)
                    other = page.get_child(other_idx)

                    # Divide one into 3 rectangles
                    draw_n_shifted(3, choice, "v")

                    # Some issue with the function calls and seeding
                    n = 4
                    shifts = []
                    choice_max = round((100/n)*1.5)
                    choice_min = round((100/n)*0.5)
                    for i in range(0, n):
                        shift_choice = np.random.randint(
                            choice_min,
                            choice_max
                        )

                        choice_max = choice_max + ((100/n) - shift_choice)
                        shifts.append(shift_choice)

                    to_add_or_remove = (100 - sum(shifts))/len(shifts)

                    normalized_shifts = []
                    for shift in shifts:
                        new_shift = shift + to_add_or_remove
                        normalized_shifts.append(new_shift/100)

                    # Divide the other into 4 rectangles
                    draw_n_shifted(4, other, "v", shifts=normalized_shifts)

    return page
