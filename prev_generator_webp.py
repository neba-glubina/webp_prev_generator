import subprocess
import random
import os
import glob

# Получение длительности видео (в секундах)
def get_video_duration(filename):
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return float(result.stdout)

# Основная функция создания WebP анимации
def create_gif_from_video(filename, output_webp, clip_count=4, total_duration=4):
    video_duration = get_video_duration(filename)
    clip_duration = total_duration / clip_count

    temp_files = []

    for i in range(clip_count):
        start_time = random.uniform(0, max(0, video_duration - clip_duration))
        temp_file = f'temp_clip_{i}.mp4'
        temp_files.append(temp_file)

        # Вырезаем отрывок с масштабированием до 720p и без потерь
        subprocess.run([
            'ffmpeg', '-ss', str(start_time), '-t', str(clip_duration), '-i', filename, 
            '-vf', 'scale=720:-2', '-c:v', 'libx264', '-crf', '0', '-c:a', 'copy', '-y', temp_file
        ])

    # Объединяем отрывки
    with open('inputs.txt', 'w') as f:
        for temp_file in temp_files:
            f.write(f"file '{temp_file}'\n")

    concat_file = 'concat.mp4'
    subprocess.run([
        'ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'inputs.txt', '-c:v', 'libx264', '-crf', '0', '-c:a', 'copy', '-y', concat_file
    ])

    # Создаём WebP анимацию с оптимизацией размера без потери качества
    subprocess.run([
        'ffmpeg', '-i', concat_file, '-c:v', 'libwebp', '-lossless', '1', 
        '-compression_level', '6', '-method', '6', '-qscale', '100',
        '-loop', '0', '-preset', 'default', '-an', '-y', output_webp
    ])

    # Удаляем временные файлы
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    if os.path.exists('inputs.txt'):
        os.remove('inputs.txt')
    if os.path.exists(concat_file):
        os.remove(concat_file)

# Альтернативная функция с дополнительными оптимизациями размера
def create_webp_optimized(filename, output_webp, clip_count=4, total_duration=4):
    video_duration = get_video_duration(filename)
    clip_duration = total_duration / clip_count

    temp_files = []

    for i in range(clip_count):
        start_time = random.uniform(0, max(0, video_duration - clip_duration))
        temp_file = f'temp_clip_{i}.mp4'
        temp_files.append(temp_file)

        # Вырезаем отрывок с масштабированием до 720p и без потерь
        subprocess.run([
            'ffmpeg', '-ss', str(start_time), '-t', str(clip_duration), '-i', filename, 
            '-vf', 'scale=720:-2', '-c:v', 'libx264', '-crf', '0', '-c:a', 'copy', '-y', temp_file
        ])

    # Объединяем отрывки
    with open('inputs.txt', 'w') as f:
        for temp_file in temp_files:
            f.write(f"file '{temp_file}'\n")

    concat_file = 'concat.mp4'
    subprocess.run([
        'ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'inputs.txt', '-c:v', 'libx264', '-crf', '0', '-c:a', 'copy', '-y', concat_file
    ])

    # Создаём WebP с максимальными оптимизациями размера
    subprocess.run([
        'ffmpeg', '-i', concat_file, '-c:v', 'libwebp', 
        '-lossless', '1', '-compression_level', '6', '-method', '6',
        '-vf', 'fps=15', '-loop', '0', '-preset', 'default', 
        '-f', 'webp', '-an', '-y', output_webp
    ])

    # Удаляем временные файлы
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    if os.path.exists('inputs.txt'):
        os.remove('inputs.txt')
    if os.path.exists(concat_file):
        os.remove(concat_file)

# Функция для конвертации всех видео файлов в папке
def convert_all_videos_in_folder(folder_path='.', use_optimized=False, clip_count=4, total_duration=4):
    """
    Конвертирует все MP4 и MOV файлы в указанной папке в WebP анимации
    
    Args:
        folder_path: путь к папке (по умолчанию текущая папка)
        use_optimized: использовать ли оптимизированную версию (True/False)
        clip_count: количество клипов
        total_duration: общая длительность в секундах
    """
    # Получаем все MP4 и MOV файлы
    video_extensions = ['*.mp4', '*.MP4', '*.mov', '*.MOV']
    video_files = []
    
    for extension in video_extensions:
        pattern = os.path.join(folder_path, '**', extension)
        video_files.extend(glob.glob(pattern, recursive=True))
    
    if not video_files:
        print(f"В папке {folder_path} не найдено видео файлов (.mp4, .mov)")
        return
    
    print(f"Найдено {len(video_files)} видео файлов для конвертации:")
    
    for i, video_file in enumerate(video_files, 1):
        print(f"\n[{i}/{len(video_files)}] Обрабатываем: {video_file}")
        
        # Создаем имя выходного файла
        file_name, file_ext = os.path.splitext(video_file)
        output_webp = f"{file_name}_preview.webp"
        
        # Проверяем, не существует ли уже файл
        if os.path.exists(output_webp):
            print(f"Файл {output_webp} уже существует, пропускаем...")
            continue
        
        try:
            # Выбираем функцию конвертации
            if use_optimized:
                create_webp_optimized(video_file, output_webp, clip_count, total_duration)
                print(f"✅ Создан оптимизированный WebP: {output_webp}")
            else:
                create_gif_from_video(video_file, output_webp, clip_count, total_duration)
                print(f"✅ Создан WebP: {output_webp}")
                
        except Exception as e:
            print(f"❌ Ошибка при обработке {video_file}: {str(e)}")
    
    print(f"\n🎉 Конвертация завершена!")

# Функция для конвертации файлов в определенных подпапках
def convert_videos_by_categories():
    """
    Конвертирует видео в папках по категориям
    """
    categories = ['3d & full cgi', 'ai', 'vfx', 'трансляции']
    
    for category in categories:
        if os.path.exists(category):
            print(f"\n📁 Обрабатываем категорию: {category}")
            convert_all_videos_in_folder(category, use_optimized=True)
        else:
            print(f"📁 Папка {category} не найдена, пропускаем...")

# Функция для создания статических изображений из WebP анимаций
def create_static_webp_from_animated(folder_path='.'):
    """
    Создает статические WebP изображения из анимированных WebP файлов,
    оставляя только первый кадр
     
    Args:
        folder_path: путь к папке (по умолчанию текущая папка)
    """
    # Получаем все WebP файлы
    webp_pattern = os.path.join(folder_path, '**', '*.webp')
    webp_files = glob.glob(webp_pattern, recursive=True)
    
    if not webp_files:
        print(f"В папке {folder_path} не найдено WebP файлов")
        return
    
    print(f"Найдено {len(webp_files)} WebP файлов для создания статических версий:")
    
    for i, webp_file in enumerate(webp_files, 1):
        print(f"\n[{i}/{len(webp_files)}] Обрабатываем: {webp_file}")
        
        # Создаем имя выходного файла
        file_name, file_ext = os.path.splitext(webp_file)
        output_static = f"{file_name}_static{file_ext}"
        
        # Проверяем, не существует ли уже файл
        if os.path.exists(output_static):
            print(f"Файл {output_static} уже существует, пропускаем...")
            continue
            
        # Проверяем, не является ли файл уже статическим
        if '_static' in file_name:
            print(f"Файл {webp_file} уже статический, пропускаем...")
            continue
        
        try:
            # Извлекаем первый кадр из анимированного WebP
            subprocess.run([
                'ffmpeg', '-i', webp_file, '-vframes', '1', '-c:v', 'libwebp',
                '-lossless', '1', '-compression_level', '6', '-method', '6',
                '-y', output_static
            ], check=True)
            
            print(f"✅ Создан статический WebP: {output_static}")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка ffmpeg при обработке {webp_file}: {str(e)}")
        except Exception as e:
            print(f"❌ Общая ошибка при обработке {webp_file}: {str(e)}")
    
    print(f"\n🎉 Создание статических изображений завершено!")

# Функция для создания статических версий по категориям
def create_static_by_categories():
    """
    Создает статические WebP изображения в папках по категориям
    """
    categories = ['3d & full cgi', 'ai', 'vfx', 'трансляции', 'пост-продакшн']
    
    for category in categories:
        if os.path.exists(category):
            print(f"\n📁 Создаем статические изображения в категории: {category}")
            create_static_webp_from_animated(category)
        else:
            print(f"📁 Папка {category} не найдена, пропускаем...")

# Примеры использования:

# 1. Конвертация одного файла (обычная версия):
# create_gif_from_video('input.mp4', 'input_preview.webp', clip_count=4, total_duration=4)

# 2. Конвертация одного файла (оптимизированная версия):
# create_webp_optimized('3d + full cgi/Parametr.mp4', '3d + full cgi/Parametr_optimized.webp', clip_count=4, total_duration=4)

# 3. Конвертация всех видео в текущей папке:
# convert_all_videos_in_folder('.', use_optimized=True)

# 4. Конвертация всех видео в определенной папке:
# convert_all_videos_in_folder('трансляции', use_optimized=True)

# 5. Конвертация по категориям (автоматически ищет папки):
# convert_videos_by_categories()

# 6. Создание статических изображений из всех WebP в текущей папке:
# create_static_webp_from_animated('.')

# 7. Создание статических изображений по категориям:
# create_static_by_categories()

# 8. Конвертация с другими параметрами:
# convert_all_videos_in_folder('.', use_optimized=True, clip_count=3, total_duration=3)

# 7. Создание статических изображений из анимированных WebP в текущей папке:
# create_static_webp_from_animated('.')

# 8. Создание статических изображений по категориям:
create_static_by_categories()
