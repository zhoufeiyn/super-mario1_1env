#!/usr/bin/env python
__author__ = 'justinarmstrong'

"""
This is an attempt to recreate the first level of
Super Mario Bros for the NES.
"""

import sys
import pygame as pg
from data.main import main
import cProfile


if __name__=='__main__':
    # 检查命令行参数
    recording_mode = '--record' in sys.argv or '-r' in sys.argv
    
    # 解析帧跳过参数
    frame_skip = 1
    if '--skip' in sys.argv:
        try:
            skip_index = sys.argv.index('--skip')
            if skip_index + 1 < len(sys.argv):
                frame_skip = int(sys.argv[skip_index + 1])
        except (ValueError, IndexError):
            print("警告: --skip 参数无效，使用默认值 1")
    
    # 解析质量参数
    quality = 'high'
    if '--quality' in sys.argv:
        try:
            quality_index = sys.argv.index('--quality')
            if quality_index + 1 < len(sys.argv):
                quality = sys.argv[quality_index + 1]
                if quality not in ['low', 'medium', 'high']:
                    print("警告: 质量参数无效，使用默认值 medium")
                    quality = 'medium'
        except IndexError:
            print("警告: --quality 参数无效，使用默认值 medium")
    
    if recording_mode:
        print("=== 录制模式已开启 ===")
        print("游戏将记录每一帧的图片和玩家动作")
        print("录制数据将保存在 recordings/ 目录下")
        print("按 Ctrl+C 或正常退出游戏来停止录制")
        print(f"帧跳过间隔: {frame_skip} (每{frame_skip}帧保存一次)")
        print(f"图片质量: {quality}")
        print("========================\n")
    
    try:
        main(recording_mode=recording_mode, frame_skip=frame_skip, quality=quality)
    except KeyboardInterrupt:
        print("\n录制已停止")
    finally:
        pg.quit()
        sys.exit()