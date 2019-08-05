import numpy as np
from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.layouts import layout, Row
from bokeh.models import (HoverTool, ColumnDataSource, SaveTool, Range1d,
                          Label, NumeralTickFormatter)
from bokeh.models.widgets import (Select, Button, TextInput, DatePicker,
                                  Panel, Tabs)
from bokeh.transform import dodge
from pybaseball import playerid_lookup, statcast_pitcher, statcast_batter
from datetime import datetime


# global variables
p_dict = {}
h_dict = {}
data = None
batter_data = None
pitcher_data = None
batter_data = None
sub_batter = None

data_cds = ColumnDataSource({'pitch': [], 'speed': [], 'result': [],
                             'count': [], 'color': [], 'plate_x': [],
                             'plate_z': []})
# define Column data source to render strike zone
strike_zone_cds = ColumnDataSource({'x': [-8.5 / 12, 8.5 / 12],
                                    'x_side1': [-8.5 / 12, -8.5 / 12],
                                    'x_side2': [8.5 / 12, 8.5 / 12],
                                    'top': [3.0, 3.0],
                                    'bottom': [1.2, 1.2],
                                    'side1': [3.0, 1.2],
                                    'side2': [1.2, 3.0]})
# CDS for pitch frequency - pitcher
pitch_cds_p = ColumnDataSource({'pitches': [], 'matchup': [], 'overall': []})
# CDS for pitch frequency - batter
pitch_cds_b = ColumnDataSource({'pitches': [], 'matchup': [], 'overall': []})


def reset_data():
    global data_cds
    global pitch_cds_p
    data_cds.data = {'pitch': [], 'speed': [], 'result': [],
                     'count': [], 'color': [], 'plate_x': [],
                     'plate_z': []}
    pitch_cds_p.data = {'pitches': [], 'matchup': [], 'overall': []}


def results(event, des):
    """
    function for formatting the event description
    """
    des_mapping = {'ball': 'Ball', 'blocked_ball': 'Ball',
                   'called_strike': 'Called Strike', 'foul': 'Foul',
                   'foul_bunt': 'Foul', 'foul_tip': 'Foul Tip',
                   'hit_by_pitch': 'HBP', 'swinging_strike': 'Swinging Strike',
                   'swinging_strike_blocked': 'Swinging strike',
                   'fielders_choice_out': "Fielder's Choice",
                   'force_out': 'Force Out',
                   'missed_bunt': 'Missed Bunt',
                   'intent_ball': 'Intentional Ball',
                   'pitchout': 'Pitchout'}
    event_mapping = {'single': 'Single', 'double': 'Double',
                     'triple': 'Triple', 'home_run': 'Home Run',
                     'field_error': 'Error', 'field_out': 'Out',
                     'grounded_into_double_play': 'Double Play',
                     'force_out': 'Force Out',
                     'fielders_choice_out': "Fielder's Choice - Out",
                     'double_play': 'Double Play',
                     'sac_fly': 'Sac Fly', 'sac_bunt': 'Sac Bunt',
                     'fielders_choice': "Fielder's Choice"}
    if des.startswith('hit_into_play'):
        try:
            return event_mapping[event]
        except KeyError:
            return event
    else:
        try:
            return des_mapping[des]
        except KeyError:
            return event


# function for returning a list of players
def getplayer(first, last):
    """
    function for getting a list of players to select from
    """
    if first == '':
        first = None
    players = playerid_lookup(last, first)
    players = players[players.mlb_played_first.notnull()]
    # TODO: figure out how to deal with players with the same name
    temp_dict = {}
    for r in players.iterrows():
        first = r[1]['name_first']
        last = r[1]['name_last']
        sid = r[1]['key_mlbam']  # statcast ID
        full = f'{first} {last} - {sid}'.title()
        temp_dict[full] = sid
    return temp_dict


def pitcher():
    """
    Gathers a list of pitchers to select from
    """
    psearch.label = 'Searching...'
    global p_dict
    first = pfirstname.value
    last = plastname.value
    p_dict = getplayer(first, last)
    pitcherselect.options = list(p_dict.keys())
    pitcherselect.value = pitcherselect.options[0]
    psearch.label = 'Search'


def hitter():
    """
    Gathers a list of batters to select from
    """
    hsearch.label = 'Searching...'
    global h_dict
    first = hfirstname.value
    last = hlastname.value
    h_dict = getplayer(first, last)
    hitterselect.options = list(h_dict.keys())
    hitterselect.value = hitterselect.options[0]
    hsearch.label = 'Search'


def filter_data():
    """
    Function for updating the figure
    """
    global data
    global pitcher_data
    global batter_data
    global sub_batter
    subdata = data  # data for the pitches plot
    suboverall_p = pitcher_data  # data for pitcher pitch frequency
    suboverall_b = batter_data  # data for batter pitch frequency
    submatchup_b = sub_batter  # data for batter pitch frequency
    # filter on balls and strikes
    if balls.value == 'All':
        pass
    else:
        count_balls = int(balls.value)
        subdata = data[data['balls'] == count_balls]
        suboverall_p = pitcher_data[pitcher_data['balls'] == count_balls]
        suboverall_b = batter_data[batter_data['balls'] == count_balls]
        submatchup_b = sub_batter[sub_batter['balls'] == count_balls]
    if strikes.value == 'All':
        pass
    else:
        count_strikes = int(strikes.value)
        subdata = subdata[subdata['strikes'] == count_strikes]
        suboverall_p = suboverall_p[suboverall_p['strikes'] == count_strikes]
        suboverall_b = suboverall_b[suboverall_b['strikes'] == count_strikes]
        submatchup_b = submatchup_b[submatchup_b['strikes'] == count_strikes]
    new_data = {'pitch': subdata['pitch_name'],
                'speed': subdata['release_speed'],
                'result': subdata['result'],
                'count': subdata['count'],
                'color': subdata['color'],
                'plate_x': subdata['plate_x'],
                'plate_z': subdata['plate_z']}
    data_cds.data = new_data
    unique_p, match_p, overall_p = pitch_frequency(suboverall_p, subdata)
    new_data_pitcher = {'pitches': unique_p,
                        'matchup': match_p,
                        'overall': overall_p}
    pitch_cds_p.data = new_data_pitcher
    unique_b, match_b, overall_b = pitch_frequency(suboverall_b, submatchup_b)

    new_data_batter = {'pitches': unique_b,
                       'matchup': match_b,
                       'overall': overall_b}
    pitch_cds_b.data = new_data_batter


def selection_update(attr, old, new):
    pass


def pitch_frequency(data, sub_data):
    """
    Function for finding the frequency of pitches
    """
    unique_pitches = tuple(np.unique(data['pitch_name']))
    try:
        perc_overall = [len(data[data['pitch_name'] == p]) / len(data)
                        for p in unique_pitches]
    # account for no matchups at all or under certain counts
    except ZeroDivisionError:
        perc_overall = np.zeros(len(unique_pitches))
    try:
        perc_matchup = [(len(sub_data[sub_data['pitch_name'] == p]) /
                         len(sub_data))
                        for p in unique_pitches]
    except ZeroDivisionError:
        # return all zeros if the event never occurs in the match up
        perc_matchup = np.zeros(len(unique_pitches))
    return unique_pitches, perc_matchup, perc_overall


def pitch_info(data):
    """
    Function for assigning pitch color and name
    """
    # pitch color dictionary
    color = {'FF': 'red', 'FT': 'red', 'FC': 'red', 'FS': 'red',
             'SI': 'red', 'CH': 'blue', 'CU': 'purple', 'CB': 'purple',
             'KC': 'purple', 'KN': 'orange', 'SL': 'green', 'PO': 'black',
             'IN': 'black', 'EP': 'black', 'SF': 'red'}
    # pitch name dictionary
    pitch_names = {'FF': 'Four-Seam Fastball', 'FT': 'Two-Seam Fastball',
                   'FC': 'Cutter', 'FS': 'Sinker', 'SI': 'Sinker',
                   'SF': 'Splitter', 'SL': 'Slider', 'CH': 'Change-Up',
                   'CB': 'Curveball', 'CU': 'Curveball', 'KC': 'Knuckle-Curve',
                   'KN': 'Knuckler', 'EP': 'Eephus', 'UN': 'Unidentified',
                   'PO': 'Pitch Out', 'XX': 'Unidentified', 'FO': 'Pitch Out'}
    pitch_color = []
    pitch_name = []
    for r in data.iterrows():
        # assign pitch color
        pitch = r[1]['pitch_type']
        try:
            pitch_color.append(color[pitch])
            pitch_name.append(pitch_names[pitch])
        except KeyError:
            pitch_color.append('black')
            pitch_name.append('Unidentified')
    data['color'] = pitch_color
    data['pitch_name'] = pitch_name
    return data


def retrieve_data():
    """
    Function for retrieving data from Statcast and performing some custom
    formatting
    """
    run_button.label = 'Running...'
    reset_data()
    global p_dict
    global h_dict
    global data
    global data_cds
    global pitch_cds_p
    global pitches_p
    global pitcher_data
    global batter_data
    global sub_batter

    # update plot title
    pitchername = pitcherselect.value.split(' -')[0]
    battername = hitterselect.value.split(' -')[0]
    plot.title.text = f'{pitchername} vs. {battername}'
    pitcher_id = p_dict[pitcherselect.value]
    hitter_id = h_dict[hitterselect.value]
    # all the data for the batter in the time frame
    batter_data_temp = statcast_batter(str(start_date.value),
                                       str(end_date.value),
                                       hitter_id)
    batter_data = pitch_info(batter_data_temp)
    # all data for the pitcher in the time frame
    pitcher_data_temp = statcast_pitcher(str(start_date.value),
                                         str(end_date.value),
                                         pitcher_id)
    pitcher_data = pitch_info(pitcher_data_temp)
    # filter to only the pitches thrown to selected batter
    data = pitcher_data[pitcher_data['batter'] == hitter_id].copy()
    sub_batter = batter_data[batter_data['pitcher'] == pitcher_id].copy()
    if len(data) == 0:
        warning_txt = 'No matchups in specified time frame'
        warning_label.text = warning_txt
    else:
        warning_label.text = ''
        result = []
        count = []
        for r in data.iterrows():
            # assign event names
            event = results(r[1]['events'], r[1]['description'])
            result.append(event)
            count_str = f"{r[1]['balls']}, {r[1]['strikes']}"
            count.append(count_str)
        data['result'] = result
        data['count'] = count
        # update column data source
        new_data = {'pitch': data['pitch_name'],
                    'speed': data['release_speed'],
                    'result': data['result'],
                    'count': data['count'],
                    'color': data['color'],
                    'plate_x': data['plate_x'],
                    'plate_z': data['plate_z']}
        data_cds.data = new_data

        # update strike zoe
        new_top = data.sz_top.sum() / len(data.sz_top)
        new_bottom = data.sz_bot.sum() / len(data.sz_bot)
        new_zone = {'x': [-8.5 / 12, 8.5 / 12],
                    'x_side1': [-8.5 / 12, -8.5 / 12],
                    'x_side2': [8.5 / 12, 8.5 / 12],
                    'top': [new_top, new_top],
                    'bottom': [new_bottom, new_bottom],
                    'side1': [new_top, new_bottom],
                    'side2': [new_bottom, new_top]}
        strike_zone_cds.data = new_zone

        # update pitch plots
        p_unique, p_matchup, p_overall = pitch_frequency(pitcher_data, data)
        pitches_p.x_range.factors = p_unique
        new_data_pitcher = {'pitches': p_unique,
                            'matchup': p_matchup,
                            'overall': p_overall}
        pitch_cds_p.data = new_data_pitcher
        b_unique, b_matchup, b_overall = pitch_frequency(batter_data,
                                                         sub_batter)
        pitches_b.x_range.factors = b_unique
        new_data_batter = {'pitches': b_unique,
                           'matchup': b_matchup,
                           'overall': b_overall}
        pitch_cds_b.data = new_data_batter
        print('Data Gathered')
    run_button.label = 'Run'


# define widgets
# pitcher search
pfirstname = TextInput(placeholder='First Name', title='Pitcher Search',
                       width=300)
plastname = TextInput(placeholder='Last Name', title=' ', width=300)
psearch = Button(label='Search', button_type='primary', width=300)
pitcherselect = Select(title='Pitcher', options=[])
pitcherselect.on_change('value', selection_update)

# hitter seartch
hfirstname = TextInput(placeholder='First Name', title='Batter Search',
                       width=300)
hlastname = TextInput(placeholder='Last Name', title=' ', width=300)
hsearch = Button(label='Search', button_type='primary', width=300)
hitterselect = Select(title='Batter', options=[])
hitterselect.on_change('value', selection_update)

# button actions
psearch.on_click(pitcher)
hsearch.on_click(hitter)

# date selectors
start_date = DatePicker(title='Start Date', min_date=datetime(2017, 4, 1),
                        max_date=datetime.now(),
                        value=datetime.now())
end_date = DatePicker(title='End Date', min_date=datetime(2017, 4, 1),
                      max_date=datetime.now(),
                      value=datetime.now())

run_button = Button(label='Run', button_type='primary', width=20)
run_button.on_click(retrieve_data)

# define the figure that shows each pitch location
plot = figure(width=400, height=500, title='Pitches')
# add strike zone lines
plot.line(x='x', y='top', line_width=3, color='grey', source=strike_zone_cds)
plot.line(x='x', y='bottom', line_width=3, color='grey',
          source=strike_zone_cds)
plot.line(x='x_side1', y='side1', line_width=3, color='grey',
          source=strike_zone_cds)
plot.line(x='x_side2', y='side2', line_width=3, color='grey',
          source=strike_zone_cds)
pitches = plot.circle(x='plate_x', y='plate_z', color='color', alpha=0.5,
                      size=10, source=data_cds)

hover = HoverTool(tooltips=[('Pitch', '@pitch'), ('Velo', '@speed',),
                            ('Result', '@result'), ('Count', '@count')],
                  renderers=[pitches])
plot.tools = [hover, SaveTool()]
plot.xgrid.grid_line_color = None
plot.ygrid.grid_line_color = None
plot.x_range = Range1d(-3.5, 3.5)
plot.y_range = Range1d(-2.5, 6)

warning_label = Label(text='',
                      x=-2.25, y=4)
plot.add_layout(warning_label, place='above')

# plot for pitches - just pitcher data
pitches_p = figure(x_range=[], y_range=Range1d(0, 1),
                   title='Pitch Frequency', height=400)
overall_p = pitches_p.vbar(x=dodge('pitches', -0.15, pitches_p.x_range),
                           top='overall', width=0.3, fill_alpha=0.5,
                           legend='Overall', source=pitch_cds_p)
matchup_p = pitches_p.vbar(x=dodge('pitches', 0.15, pitches_p.x_range),
                           top='matchup', width=0.3, fill_color='red',
                           fill_alpha=0.5, legend='Matchup',
                           source=pitch_cds_p)
pitches_p.xgrid.grid_line_color = None
pitches_p.yaxis[0].formatter = NumeralTickFormatter(format='0%')
pitches_p.xaxis.major_label_orientation = 45

# plot for pitches - just batter data
pitches_b = figure(x_range=[], y_range=Range1d(0, 1),
                   title='Pitch Frequency', height=400)
overall_b = pitches_b.vbar(x=dodge('pitches', -0.15, pitches_b.x_range),
                           top='overall', width=0.3, fill_alpha=0.5,
                           legend='Overall', source=pitch_cds_b)
matchup_b = pitches_b.vbar(x=dodge('pitches', 0.15, pitches_b.x_range),
                           top='matchup', width=0.3, fill_color='red',
                           fill_alpha=0.5, legend='Matchup',
                           source=pitch_cds_b)
pitches_b.xgrid.grid_line_color = None
pitches_b.yaxis[0].formatter = NumeralTickFormatter(format='0%')
pitches_b.xaxis.major_label_orientation = 45
# add hover tools
overall_hover_p = HoverTool(tooltips=[('Freq.', '@overall{0.00%}')],
                            renderers=[overall_p])
matchup_hover_p = HoverTool(tooltips=[('Freq.', '@matchup{0.00%}')],
                            renderers=[matchup_p])
overall_hover_b = HoverTool(tooltips=[('Freq.', '@overall{0.00%}')],
                            renderers=[overall_b])
matchup_hover_b = HoverTool(tooltips=[('Freq.', '@matchup{0.00%}')],
                            renderers=[matchup_b])

pitches_p.tools = [overall_hover_p, matchup_hover_p, SaveTool()]
pitches_b.tools = [overall_hover_b, matchup_hover_b, SaveTool()]

# tab pitch data
tab1 = Panel(child=pitches_p, title='Pitcher')
tab2 = Panel(child=pitches_b, title='Batter')
pitch_tabs = Tabs(tabs=[tab1, tab2])

# filters for count
balls = Select(title='Balls', options=['All', '0', '1', '2', '3'], value='All',
               width=60)
strikes = Select(title='Strikes', options=['All', '0', '1', '2'], value='All',
                 width=60)
balls.on_change('value', lambda attr, old, new: filter_data())
strikes.on_change('value', lambda attr, old, new: filter_data())

l = layout([[Row(pfirstname, plastname, psearch)],
            [pitcherselect],
            [Row(hfirstname, hlastname, hsearch)],
            [hitterselect],
            [start_date, end_date],
            [run_button],
            [balls, strikes],
            [plot, pitch_tabs]
            ], sizing_mode='fixed')

curdoc().add_root(l)
