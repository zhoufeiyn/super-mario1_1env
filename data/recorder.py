__author__ = 'justinarmstrong'

import os
import json
import pygame as pg
from . import tools
from . import constants as c
import time
import threading
import queue

class Recorder:
    """录制器类，用于记录游戏帧和玩家动作"""
    
    def __init__(self, recording_mode=False, frame_skip=1, quality='medium'):
        self.recording_mode = recording_mode
        self.frame_data = []
        self.frame_count = 0
        self.start_time = None
        self.frame_skip = frame_skip  # 帧跳过间隔，1=每帧都保存，2=每2帧保存一次
        self.quality = quality  # 图片质量: 'low', 'medium', 'high'
        self.save_frame_count = 0  # 实际保存的帧数
        
        # 异步保存相关
        self.save_queue = queue.Queue()
        self.save_thread = None
        self.save_thread_running = False
        
        # 创建录制目录
        if self.recording_mode:
            timestamp = int(time.time())
            self.recording_dir = f"recordings/recording_{timestamp}"
            os.makedirs(self.recording_dir, exist_ok=True)
            os.makedirs(f"{self.recording_dir}/frames", exist_ok=True)
            print(f"录制模式已开启，保存路径: {self.recording_dir}")
            print(f"帧跳过间隔: {self.frame_skip} (每{self.frame_skip}帧保存一次)")
            print(f"图片质量: {self.quality}")
    
    def start_recording(self):
        """开始录制"""
        if self.recording_mode:
            self.start_time = time.time()
            self.frame_data = []
            self.frame_count = 0
            self.save_frame_count = 0
            
            # 启动异步保存线程
            self.save_thread_running = True
            self.save_thread = threading.Thread(target=self._save_worker)
            self.save_thread.daemon = True
            self.save_thread.start()
            
            print("开始录制...")
    
    def stop_recording(self):
        """停止录制并保存数据"""
        if self.recording_mode and self.frame_data:
            # 停止异步保存线程
            self.save_thread_running = False
            if self.save_thread:
                self.save_thread.join(timeout=5.0)  # 等待最多5秒
            
            self.save_recording_data()
            print(f"录制完成！共录制 {self.frame_count} 帧")
            print(f"实际保存图片 {self.save_frame_count} 张")
            print(f"数据已保存到: {self.recording_dir}")
    
    def _save_worker(self):
        """异步保存工作线程"""
        while self.save_thread_running:
            try:
                # 从队列中获取保存任务
                save_task = self.save_queue.get(timeout=0.1)
                if save_task is None:  # 结束信号
                    break
                
                surface, frame_path, frame_info = save_task
                
                # 执行实际的保存操作
                try:
                    if self.quality == 'high':
                        pg.image.save(surface, frame_path)
                    else:
                        surface_to_save = self.prepare_surface_for_save(surface)
                        pg.image.save(surface_to_save, frame_path)
                    
                    frame_info['frame_filename'] = f"frame_{self.save_frame_count:06d}.png"
                    self.save_frame_count += 1
                except Exception as e:
                    print(f"保存图片失败: {e}")
                    frame_info['frame_filename'] = None
                
                self.save_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"保存线程错误: {e}")
                break
    
    def record_frame(self, keys, mario_state, mario_dead, screen_surface):
        """记录当前帧的数据"""
        if not self.recording_mode:
            return
        
        # 编码动作
        action_code = self.encode_action(keys)
        
        # 检查是否需要跳过这一帧
        should_save_frame = (self.frame_count % self.frame_skip == 0)
        
        # 记录帧数据（每帧都记录，但图片可能跳过）
        frame_info = {
            'frame_id': self.frame_count,
            'timestamp': time.time() - self.start_time if self.start_time else 0,
            'action_code': action_code,
            'action_binary': bin(action_code),
            'action_names': self.decode_action(action_code),
            'mario_state': mario_state,
            'mario_dead': mario_dead,
            'frame_saved': should_save_frame  # 标记是否保存了图片
        }
        
        # 如果需要保存图片
        if should_save_frame:
            frame_filename = f"frame_{self.save_frame_count:06d}.png"
            frame_path = f"{self.recording_dir}/frames/{frame_filename}"
            
            # 创建surface的副本用于异步保存
            surface_copy = screen_surface.copy()
            
            # 将保存任务加入队列
            try:
                self.save_queue.put((surface_copy, frame_path, frame_info), timeout=0.01)
            except queue.Full:
                # 如果队列满了，跳过这一帧
                frame_info['frame_filename'] = None
                print("保存队列已满，跳过当前帧")
        else:
            frame_info['frame_filename'] = None
        
        self.frame_data.append(frame_info)
        self.frame_count += 1
    
    def encode_action(self, keys):
        """将键盘输入编码为动作值
        编码规则：每一帧的动作 = 所有按下键的位或运算（OR运算）
        """
        action = 0
        
        # 左右移动（互斥）
        if keys[tools.keybinding['left']]:
            action |= 1  # LEFT
        elif keys[tools.keybinding['right']]:
            action |= 2  # RIGHT
        
        # 跳跃（可与其他动作组合）
        if keys[tools.keybinding['jump']]:
            action |= 4  # JUMP
        
        # 动作键（可与其他动作组合）
        if keys[tools.keybinding['action']]:
            action |= 8  # ACTION
        
        # 蹲下（可与其他动作组合）
        if keys[tools.keybinding['down']]:
            action |= 16  # DOWN
        
        return action
    
    def prepare_surface_for_save(self, surface):
        """根据质量设置准备要保存的surface"""
        if self.quality == 'low':
            # 低质量：缩小到50%
            new_width = int(surface.get_width() * 0.5)
            new_height = int(surface.get_height() * 0.5)
            return pg.transform.scale(surface, (new_width, new_height))
        elif self.quality == 'high':
            # 高质量：保持原尺寸
            return surface
        else:  # medium
            # 中等质量：缩小到75%
            new_width = int(surface.get_width() * 0.75)
            new_height = int(surface.get_height() * 0.75)
            return pg.transform.scale(surface, (new_width, new_height))
    
    def decode_action(self, action_code):
        """将动作值解码为可读的动作描述"""
        actions = []
        
        if action_code & 1:  # LEFT
            actions.append("LEFT")
        elif action_code & 2:  # RIGHT (注意是elif)
            actions.append("RIGHT")
        
        if action_code & 4:  # JUMP
            actions.append("JUMP")
        
        if action_code & 8:  # ACTION
            actions.append("ACTION")
        
        if action_code & 16:  # DOWN
            actions.append("DOWN")
        
        return actions if actions else ["NONE"]
    
    def save_recording_data(self):
        """保存录制数据到JSON文件"""
        recording_info = {
            'recording_info': {
                'total_frames': self.frame_count,
                'duration': time.time() - self.start_time if self.start_time else 0,
                'recording_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'game_version': 'Mario Level 1'
            },
            'frame_data': self.frame_data
        }
        
        # 保存到JSON文件
        json_path = f"{self.recording_dir}/recording_data.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(recording_info, f, indent=2, ensure_ascii=False)
        
        # 保存动作统计
        self.save_action_statistics()
    
    def save_action_statistics(self):
        """保存动作统计信息"""
        action_counts = {}
        state_counts = {}
        
        for frame in self.frame_data:
            action_key = str(frame['action_code'])
            if action_key not in action_counts:
                action_counts[action_key] = 0
            action_counts[action_key] += 1
            
            state_key = frame['mario_state']
            if state_key not in state_counts:
                state_counts[state_key] = 0
            state_counts[state_key] += 1
        
        stats = {
            'action_statistics': action_counts,
            'state_statistics': state_counts,
            'action_descriptions': {
                str(self.encode_action({tools.keybinding['left']: True})): "LEFT",
                str(self.encode_action({tools.keybinding['right']: True})): "RIGHT",
                str(self.encode_action({tools.keybinding['jump']: True})): "JUMP",
                str(self.encode_action({tools.keybinding['action']: True})): "ACTION",
                str(self.encode_action({tools.keybinding['down']: True})): "DOWN",
                "0": "NONE"
            }
        }
        
        stats_path = f"{self.recording_dir}/statistics.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
