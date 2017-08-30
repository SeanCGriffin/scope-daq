import numpy as np
import visa

VISA_RM = visa.ResourceManager('@py')

def connect_to_ethernet_device(visa_resource_manager=VISA_RM, address="10.10.10.10"):
    '''
    Connect to an ethernet device with specified IP.
    '''
    resource_str = 'TCPIP0::{0:s}::inst0::INSTR'.format(address)
    scope = visa_resource_manager.open_resource(resource_str)

    return scope


def read_config(handler, verbose=False):
    '''
    Load full waveform configuration data from a device and 
    fill a dictrionary with it. 
    '''
    command = ':WFMO?'
    config = handler.query(command)
    config_dict = {}

    for parameter in config.split(';'):
        key, val = parameter.split(' ', 1)
        config_dict[key] = val
        if verbose:
            print("{0:s} : {1:s}".format(key, val))

def set_trigger(handler, channel, threshold, edge="FALL"):
    '''
    Set the trigger parameters for the oscilloscope.
    Threshold is in millivolts. 
    '''
    handler.write(":TRIG:A:EDGE:SOU CH{0:d}".format(channel))
    handler.write(":TRIG:A:EDGE:SLOPE {0:s}".format(edge))
    handler.write(':TRIG:A:LEVEL:CH{0:d} {1:f}'.format(channel, threshold/1000.))

def get_source_channel(handler, verbose=False):
    '''
    Returns the data channel from the scope.
    '''
    channel = handler.query(":DATA:SOURCE?").rstrip('\n').split(" ")
    channel = int(channel[-1][-1])

    if verbose:
        print("Data source channel: {0:d}".format(channel))

    return channel

def set_source_channel(handler, channel):
    '''
    Set the data return channel on the scope.
    '''
    handler.write(":DATA:SOURCE {0:d}".format(channel))

def read_scaling_config(handler, verbose=False):
    '''
    Read the configuration information required to correctly scale the x- and y- axes in CURVe data.
    '''

    channel = get_source_channel(handler, verbose)
    prefix = ':WFMOutpre:'
    command_list = ['NR_PT?', 
                    'XUNIT?',
                    'XZERO?',
                    'XINCR?',
                    'YUNIT?',
                    'YZERO?',
                    'YMULT?',
                    'YOFF?',
                    
                   ]

    scaling_dict = {}
    for command in command_list:
        val = handler.query(prefix + command)
        #drop the '?' and parse the query return
        scaling_dict[command[0:-1]] = val.rstrip("\n").split(" ")[-1] 
        
    scaling_dict['channel'] = channel
    scaling_dict['record_length'] = handler.query('HORizontal:RECOrdlength?').rstrip("\n").split(" ")[-1] 
    if verbose:
        for key in scaling_dict:
            print(key, scaling_dict[key])

    return scaling_dict    
    
def scale_data(scaling_dict, curve):
    '''
    Using the scaling dictionary, return a 2D array containing X and Y values. 
    '''

    x_zero = float(scaling_dict['XZERO'])
    x_incr = float(scaling_dict['XINCR'])
    y_zero = float(scaling_dict['YZERO'])
    y_mult = float(scaling_dict['YMULT'])
    y_offset = float(scaling_dict['YOFF'])

    x_points = np.empty(len(curve))
    for i in range(len(curve)):
        x_points[i] = x_zero + x_incr * i

    y_points = (curve - y_offset) * y_mult + y_zero

    return x_points, y_points

def read_trace(handler):
    '''
    Read an oscilloscope trace.
    '''

    curve = np.array(handler.query("CURVE?").rstrip('\n').split(' ', 1)[-1].split(','), dtype=float)
    #x,y = MSO.scale_data(scaling_dict, curve)
    return curve

def set_time_axis(handler, scale=100.e-9, position=0, readout_length=1000, mode=0, verbose=False):
    '''
    Set the time axis characteristics for the scope. 
    Parameters: 
        scale : Horizontal scale in s
        position : readout window position in percent. 0 places trigger at center of readout, 
            60 places it one division further to the left.
        readout_length: Readout length in samples; 1000, 10,000, etc.
        mode: To use the position argument as a position knob, use mode=0 (the default).
        verbose: verbose?


    '''
    prefix = ':HOR:'
    handler.write(prefix+':DELAY:MODE {0:d}'.format(mode))
    handler.write(prefix+'POS {0:f}'.format(position))
    handler.write(prefix+'RECO {0:f}'.format(readout_length))
    handler.write(prefix+'SCA {0:f}'.format(scale))



    if verbose:
        print("Horizontal configuration information: ")
        for i in handler.query(":HOR?").rstrip('\n').split(';'):
            print(i)

def set_vertical_axis(handler, scale, position, verbose):

    '''
    This function is incomplete. 
    '''

    if verbose:
        print("Vertical configuration information:")

