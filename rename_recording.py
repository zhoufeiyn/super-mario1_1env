#!/usr/bin/env python
"""
录制文件重命名工具
用法: python rename_recording.py --user zf --f recording_1761098154
"""

import os
import json
import argparse
import sys


def load_recording_data(recording_dir):
    """加载录制数据JSON文件"""
    json_path = os.path.join(recording_dir, "recording_data.json")
    
    if not os.path.exists(json_path):
        print(f"错误: 找不到文件 {json_path}")
        return None
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        print(f"JSON格式错误: {e}")
        print("尝试修复JSON文件...")
        return try_fix_json(json_path)
    except Exception as e:
        print(f"错误: 无法读取JSON文件 - {e}")
        return None


def try_fix_json(json_path):
    """尝试修复损坏的JSON文件"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试找到最后一个完整的frame_data条目
        lines = content.split('\n')
        fixed_lines = []
        bracket_count = 0
        in_frame_data = False
        
        for i, line in enumerate(lines):
            fixed_lines.append(line)
            
            # 计算括号数量
            bracket_count += line.count('{') - line.count('}')
            
            # 检查是否在frame_data数组中
            if '"frame_data":' in line:
                in_frame_data = True
            
            # 如果在frame_data中且括号不平衡，可能找到了截断点
            if in_frame_data and bracket_count < 0:
                print(f"在第 {i+1} 行发现可能的截断点")
                # 尝试修复
                fixed_lines.append('    ]')
                fixed_lines.append('}')
                break
        
        # 如果文件没有正确结束，添加结束符
        if bracket_count > 0:
            for _ in range(bracket_count):
                fixed_lines.append('}')
        
        # 写回修复后的内容
        fixed_content = '\n'.join(fixed_lines)
        
        # 备份原文件
        backup_path = json_path + '.backup'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"原文件已备份到: {backup_path}")
        
        # 写入修复后的文件
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print("JSON文件修复完成，尝试重新加载...")
        
        # 重新尝试加载
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
        
    except Exception as e:
        print(f"修复JSON文件失败: {e}")
        return None


def load_recording_data_simple(recording_dir):
    """简单加载录制数据，忽略JSON错误"""
    json_path = os.path.join(recording_dir, "recording_data.json")
    
    if not os.path.exists(json_path):
        print(f"错误: 找不到文件 {json_path}")
        return None
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尝试手动解析frame_data部分
        frame_data = []
        
        # 查找frame_data数组
        start_marker = '"frame_data": ['
        end_marker = ']'
        
        start_pos = content.find(start_marker)
        if start_pos == -1:
            print("错误: 找不到frame_data数组")
            return None
        
        start_pos += len(start_marker)
        
        # 查找frame_data数组的结束位置
        bracket_count = 0
        end_pos = start_pos
        
        for i in range(start_pos, len(content)):
            if content[i] == '{':
                bracket_count += 1
            elif content[i] == '}':
                bracket_count -= 1
                if bracket_count == 0:
                    # 找到一个完整的frame对象
                    frame_text = content[start_pos:i+1].strip()
                    if frame_text.startswith(','):
                        frame_text = frame_text[1:].strip()
                    
                    try:
                        frame_obj = json.loads(frame_text)
                        # 确保frame_filename字段存在
                        if 'frame_filename' not in frame_obj:
                            frame_obj['frame_filename'] = None
                        frame_data.append(frame_obj)
                    except:
                        # 忽略解析失败的frame
                        pass
                    
                    start_pos = i + 1
        
        if not frame_data:
            print("错误: 无法解析任何帧数据")
            return None
        
        print(f"成功解析 {len(frame_data)} 个帧数据")
        
        # 创建简化的数据结构
        data = {
            'recording_info': {
                'total_frames': len(frame_data),
                'duration': 0.0,
                'recording_time': 'unknown',
                'game_version': 'Mario Level 1'
            },
            'frame_data': frame_data
        }
        
        return data
        
    except Exception as e:
        print(f"简单解析也失败: {e}")
        return None


def rename_frames(user_name, recording_dir, frame_data):
    """重命名帧图片文件"""
    frames_dir = os.path.join(recording_dir, "frames")
    
    if not os.path.exists(frames_dir):
        print(f"错误: 找不到frames目录 {frames_dir}")
        return False, []
    
    print(f"开始重命名 {len(frame_data)} 个文件...")
    
    renamed_count = 0
    error_count = 0
    skipped_count = 0
    failed_frames = []  # 记录失败的帧信息
    
    for frame_info in frame_data:
        frame_id = frame_info['frame_id']
        action_code = frame_info['action_code']
        mario_dead = frame_info['mario_dead']
        old_filename = frame_info.get('frame_filename')  # 使用get方法避免KeyError
        
        # 检查old_filename是否为None
        if old_filename is None:
            skipped_count += 1
            continue
        
        # 生成新文件名
        # 死亡状态: True=0, False=1
        death_status = 0 if mario_dead else 1
        
        # 新文件名格式: user_fxxx_axxx_ntxxx.png
        new_filename = f"{user_name}_f{frame_id}_a{action_code}_nt{death_status}.png"
        
        old_path = os.path.join(frames_dir, old_filename)
        new_path = os.path.join(frames_dir, new_filename)
        
        try:
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
                renamed_count += 1
            else:
                error_count += 1
                # 记录失败的帧信息
                failed_frames.append({
                    'frame_id': frame_id,
                    'error_reason': '文件不存在'
                })
        except Exception as e:
            error_count += 1
            # 记录失败的帧信息
            failed_frames.append({
                'frame_id': frame_id,
                'error_reason': str(e)
            })
    
    print(f"\n重命名完成!")
    print(f"成功: {renamed_count} 个文件")
    print(f"失败: {error_count} 个文件")
    print(f"跳过: {skipped_count} 个文件 (无对应图片)")
    
    return error_count == 0, failed_frames


def update_json_data(recording_dir, frame_data, user_name):
    """更新JSON文件中的文件名信息"""
    json_path = os.path.join(recording_dir, "recording_data.json")
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 更新帧数据中的文件名
        for i, frame_info in enumerate(frame_data):
            frame_id = frame_info['frame_id']
            action_code = frame_info['action_code']
            mario_dead = frame_info['mario_dead']
            
            # 生成新文件名
            death_status = 0 if mario_dead else 1
            new_filename = f"{user_name}_f{frame_id}_a{action_code}_nt{death_status}.png"
            
            # 更新JSON数据（只有当原文件名不为None时才更新）
            if frame_info.get('frame_filename') is not None:
                data['frame_data'][i]['frame_filename'] = new_filename
            else:
                data['frame_data'][i]['frame_filename'] = None
        
        # 添加用户信息
        data['recording_info']['user_name'] = user_name
        data['recording_info']['naming_format'] = 'user_fxxx_axxx_ntxxx.png'
        
        # 保存更新后的JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"JSON文件已更新: {json_path}")
        return True
        
    except Exception as e:
        print(f"错误: 更新JSON文件失败 - {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='重命名录制文件')
    parser.add_argument('--user', required=True, help='用户名')
    parser.add_argument('--f', required=True, help='录制目录名 (如: recording_1761098154)')
    
    args = parser.parse_args()
    
    user_name = args.user
    recording_folder = args.f
    
    # 构建录制目录路径
    recording_dir = os.path.join("recordings", recording_folder)
    
    print(f"用户: {user_name}")
    print(f"录制目录: {recording_dir}")
    print("=" * 50)
    
    # 检查录制目录是否存在
    if not os.path.exists(recording_dir):
        print(f"错误: 录制目录不存在 {recording_dir}")
        sys.exit(1)
    
    # 加载录制数据
    print("加载录制数据...")
    data = load_recording_data(recording_dir)
    if not data:
        print("\n尝试使用简单解析模式...")
        data = load_recording_data_simple(recording_dir)
        if not data:
            print("所有解析方法都失败了")
            sys.exit(1)
    
    frame_data = data.get('frame_data', [])
    if not frame_data:
        print("错误: 没有找到帧数据")
        sys.exit(1)
    
    print(f"找到 {len(frame_data)} 帧数据")
    
    # 显示一些示例数据
    print("\n示例数据:")
    for i in range(min(3, len(frame_data))):
        frame = frame_data[i]
        print(f"  帧 {frame['frame_id']}: action={frame['action_code']}, dead={frame['mario_dead']}")
    
    # 确认操作
    print(f"\n准备重命名 {len(frame_data)} 个文件")
    confirm = input("是否继续? (y/N): ").strip().lower()
    if confirm != 'y':
        print("操作已取消")
        sys.exit(0)
    
    # 重命名文件
    print("\n开始重命名...")
    success, failed_frames = rename_frames(user_name, recording_dir, frame_data)
    
    if success:
        # 更新JSON文件
        print("\n更新JSON文件...")
        update_json_data(recording_dir, frame_data, user_name)
        print("\n✅ 重命名完成!")
    else:
        print("\n❌ 重命名过程中出现错误")
        
        # 显示失败的帧信息
        if failed_frames:
            print(f"\n失败的帧 (共 {len(failed_frames)} 个):")
            print("=" * 50)
            for failed_frame in failed_frames:
                print(f"帧ID: {failed_frame['frame_id']} - 失败原因: {failed_frame['error_reason']}")
        
        sys.exit(1)


if __name__ == '__main__':
    main()
