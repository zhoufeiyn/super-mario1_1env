__author__ = 'justinarmstrong'

from . import setup,tools
from .states import main_menu,load_screen,level1
from . import constants as c
from .recorder import Recorder


def main(recording_mode=False, frame_skip=1, quality='medium'):
    """Add states to control here.
    
    Args:
        recording_mode (bool): 是否开启录制模式
        frame_skip (int): 帧跳过间隔，1=每帧都保存，2=每2帧保存一次
        quality (str): 图片质量 'low', 'medium', 'high'
    """
    # 创建录制器
    recorder = Recorder(recording_mode, frame_skip, quality)
    
    run_it = tools.Control(setup.ORIGINAL_CAPTION, recorder)
    state_dict = {c.MAIN_MENU: main_menu.Menu(),
                  c.LOAD_SCREEN: load_screen.LoadScreen(),
                  c.TIME_OUT: load_screen.TimeOut(),
                  c.GAME_OVER: load_screen.GameOver(),
                  c.LEVEL1: level1.Level1()}

    run_it.setup_states(state_dict, c.MAIN_MENU)
    run_it.main()



