import os
import re
import json
import argparse
import pycountry
import urllib.request

from fixes import country_fixes

def get_country_list():
    """ Retrieve a list of countries and statuses from smartraveller.gov.au """
    url = "http://smartraveller.gov.au/countries/pages/list.aspx"
    country_list_html = urllib.request.urlopen(url)
    return country_list_html.read().decode("UTF-8")


def convert_to_png(scale):
    try:
        import cairosvg
    except BaseException as e:
        print("{}\nCairosvg required to output PNG file!".format(e))
        return

    cairosvg.svg2png(url="output.svg",
                     write_to="output.png",
                     parent_width=1024,
                     parent_height=660,
                     scale=int(arguments.scale))


def get_map_file(arguments):
    if arguments.high_quality:
        map_file = "hq.svg"
    else:
        map_file = "sq.svg"
    return os.path.join("resources", map_file)


def main(arguments):
    # The rgb vals of each warning (green, yellow, orange, red) smartraveller uses
    colours = { "normal":    (152, 211, 155),
                "caution":   (254, 230, 134),
                "warning":   (249, 172, 95),
                "danger":    (229, 117, 116),
                "australia": (0, 0, 0) }

    # Find the correct JSON data in the page downloaded and read.
    countries_json = json.loads(re.findall(r"\[{.*}\]", get_country_list())[2])

    # Initialize a list of all countries on smartraveller
    countries = [("AU", "australia")]

    # For each country in scraped JSON get the necessary fields into a nice array
    for index, item in enumerate(countries_json):
        # Loads the advice levels for the specified country
        advisory = json.loads(item["Smartraveller_x0020_Advice_x0020_Levels"])
        # Attempt to look up country code using pycountry, on failure looks CC
        # in country_fixes.
        try:
            ccode = pycountry.countries.lookup(item["Title"]).alpha_2
        except LookupError:
            ccode = country_fixes[item["Title"]]

        # Obtain the current warning level for each country, if one exists
        try:
            advisory = advisory["items"][0]['level']
        except IndexError:
            advisory = None

        countries.append((ccode, advisory))

    # Read in the entire map resource (Done early to determine map code style)
    with open(get_map_file(arguments)) as map_file:
        world_map = map_file.read()

    # Create an array that will store all our override fill colours for the svg map
    code = list()

    # Replace the python string with the code array we created, prepended with
    # correct indentation to make it slightly neater
    for ccode, advisory in countries:
        if advisory != None:
            ccolour = "rgb({},{},{})".format(*colours[advisory])
            code.append("#{} {{fill: {};}}".format(ccode, ccolour))

    world_map = world_map.replace("<!-- PYTHON Style1 -->", "\n".join(code))

    # Write the output
    with open("output.svg", "w") as out_file:
        out_file.write(world_map)

    # If conversion to png is required
    if arguments.image:
        convert_to_png(arguments.scale)


if __name__ == "__main__":
    args = argparse.ArgumentParser()

    args.add_argument("-q", "--high-quality",
                      action="store_true",
                      default=False,
                      help="Use a high quality map file.")

    args.add_argument("-i", "--image",
                      action="store_true",
                      default=False,
                      help="Render a png version of the output.")

    args.add_argument("-s", "--scale",
                      action="store",
                      default=1,
                      help="Select the scale of the PNG output.")

    arguments = args.parse_args()

    main(args.parse_args())
