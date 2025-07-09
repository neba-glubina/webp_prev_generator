import subprocess
import random
import os
import glob
from PIL import Image

# Получение длительности видео (в секундах)
def get_video_duration(filename):
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return float(result.stdout)

# Основная функция создания WebP анимации (оптимизированная версия)
def create_webp_preview(filename, output_webp, clip_count=4, total_duration=4):
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

    # Создаём WebP с оптимизациями размера
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
def convert_all_videos_to_webp(folder_path='.', clip_count=4, total_duration=4):
    """
    Конвертирует все MP4 и MOV файлы в указанной папке в WebP анимации
    
    Args:
        folder_path: путь к папке (по умолчанию текущая папка)
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
            create_webp_preview(video_file, output_webp, clip_count, total_duration)
            print(f"✅ Создан WebP: {output_webp}")
                
        except Exception as e:
            print(f"❌ Ошибка при обработке {video_file}: {str(e)}")
    
    print(f"\n🎉 Конвертация завершена!")

# Функция для создания статических изображений с помощью PIL
def create_static_with_pil(folder_path='.'):
    """
    Создает статические изображения из анимированных WebP файлов используя PIL
    """
    try:
        from PIL import Image
    except ImportError:
        print("❌ Ошибка: Установите Pillow командой: pip install Pillow")
        return
    
    # Получаем все WebP файлы
    webp_pattern = os.path.join(folder_path, '**', '*.webp')
    webp_files = glob.glob(webp_pattern, recursive=True)
    
    if not webp_files:
        print(f"В папке {folder_path} не найдено WebP файлов")
        return
    
    print(f"Найдено {len(webp_files)} WebP файлов для создания статических версий с PIL:")
    
    for i, webp_file in enumerate(webp_files, 1):
        print(f"\n[{i}/{len(webp_files)}] Обрабатываем: {webp_file}")
        
        # Создаем имя выходного файла
        file_name, file_ext = os.path.splitext(webp_file)
        
        # Проверяем, не является ли файл уже статическим
        if '_static' in file_name:
            print(f"Файл {webp_file} уже статический, пропускаем...")
            continue
        
        output_webp = f"{file_name}_static.webp"
        output_png = f"{file_name}_static.png"
        output_jpg = f"{file_name}_static.jpg"
        
        # Проверяем, не существуют ли уже файлы
        if os.path.exists(output_webp) or os.path.exists(output_png) or os.path.exists(output_jpg):
            print(f"Статический файл уже существует, пропускаем...")
            continue
        
        try:
            # Открываем WebP файл
            with Image.open(webp_file) as img:
                # Получаем первый кадр
                first_frame = img.copy()
                
                # Сохраняем в трех форматах для максимальной совместимости
                
                # WebP (статический)
                first_frame.save(output_webp, 'WEBP', quality=100, lossless=True)
                print(f"✅ Создан статический WebP: {output_webp}")
                
                # PNG (максимальная совместимость)
                first_frame.save(output_png, 'PNG', optimize=True)
                print(f"✅ Создан статический PNG: {output_png}")
                
                # JPG (минимальный размер)
                if first_frame.mode in ('RGBA', 'LA', 'P'):
                    # Конвертируем в RGB для JPG
                    rgb_img = Image.new('RGB', first_frame.size, (255, 255, 255))
                    if first_frame.mode == 'P':
                        first_frame = first_frame.convert('RGBA')
                    rgb_img.paste(first_frame, mask=first_frame.split()[-1] if first_frame.mode in ('RGBA', 'LA') else None)
                    first_frame = rgb_img
                
                first_frame.save(output_jpg, 'JPEG', quality=95, optimize=True)
                print(f"✅ Создан статический JPG: {output_jpg}")
                
        except Exception as e:
            print(f"❌ Ошибка PIL при обработке {webp_file}: {str(e)}")
            # Если PIL не работает, попробуем альтернативный метод
            try:
                print("Пробуем альтернативный метод через imageio...")
                import imageio
                reader = imageio.get_reader(webp_file)
                first_frame = reader.get_data(0)
                imageio.imwrite(output_png, first_frame)
                print(f"✅ Создан PNG через imageio: {output_png}")
            except ImportError:
                print("❌ Для альтернативного метода установите: pip install imageio")
            except Exception as e2:
                print(f"❌ Альтернативный метод также не сработал: {str(e2)}")
    
    print(f"\n🎉 Создание статических изображений завершено!")

# Функция для конвертации по категориям
def convert_videos_by_categories():
    """
    Конвертирует видео в папках по категориям
    """
    categories = ['3d & full cgi', 'ai', 'vfx', 'трансляции', 'пост-продакшн']
    
    for category in categories:
        if os.path.exists(category):
            print(f"\n📁 Обрабатываем категорию: {category}")
            convert_all_videos_to_webp(category)
        else:
            print(f"📁 Папка {category} не найдена, пропускаем...")

# Функция для создания статических изображений по категориям
def create_static_by_categories():
    """
    Создает статические изображения в папках по категориям
    """
    categories = ['3d & full cgi', 'ai', 'vfx', 'трансляции', 'пост-продакшн']
    
    for category in categories:
        if os.path.exists(category):
            print(f"\n📁 Создаем статические изображения в категории: {category}")
            create_static_with_pil(category)
        else:
            print(f"📁 Папка {category} не найдена, пропускаем...")

# Примеры использования:

# 1. Конвертация одного файла:
# create_webp_preview('input.mp4', 'input_preview.webp', clip_count=4, total_duration=4)

# 2. Конвертация всех видео в текущей папке:
# convert_all_videos_to_webp('.')

# 3. Конвертация всех видео в определенной папке:
convert_all_videos_to_webp('./tst')

# 4. Конвертация по категориям:
# convert_videos_by_categories()

# 5. Создание статических изображений из WebP:
create_static_with_pil('./tst')

# 6. Создание статических изображений по категориям:
# create_static_by_categories()
