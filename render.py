import sys
import os
import errno
import subprocess
import datetime
import pickle
import multiprocessing
import itertools
import Queue
from PIL import Image, ImageFont, ImageDraw


CROP_SIZE = 700
CROP_2 = CROP_SIZE / 2
OUTPUT_DIMS = (480,) * 2

# Limit workers since this is more disk I/O limited.
NUM_WORKERS = 4

input_base = 'frames'
output_subdir = 'render'

font = ImageFont.truetype('LiberationSans-Regular.ttf', 24)

render_command_template = (
    'ffmpeg -i %s/%%03d.jpg '
    '-y -vcodec libx264 -pix_fmt yuv420p -crf 22 -an '
    '%s'
    )
faststart_command_template ='qt-faststart %s %s'


def main(argv):
    global pool, well_dirs, map_args, result
    pool = multiprocessing.Pool(processes=NUM_WORKERS)
    manager = multiprocessing.Manager()
    queue = manager.Queue()
    well_dirs = sorted(os.listdir(input_base))
    map_args = itertools.product(well_dirs, [queue])
    result = pool.map_async(render_well_worker, map_args)
    num_complete = 0
    while not result.ready():
        try:
            (well, msg) = queue.get(timeout=0.1)
            print '%s: %s' % (well, msg)
            if msg == '<<< END':
                num_complete += 1
                pct_complete = num_complete * 100 / len(well_dirs)
                print '\n=== TOTAL: %d/%d (%d%%) completed ===\n' % \
                    (num_complete, len(well_dirs), pct_complete)
        except Queue.Empty:
            pass
        except KeyboardInterrupt:
            pool.terminate()
            raise


def render_well_worker(args):
    well_dir, queue = args

    def log(*values):
        msg = ' '.join(map(str, values))
        if queue:
            queue.put((well_dir, msg))
        else:
            print msg

    log('>>> BEGIN')
    input_path = os.path.join(input_base, well_dir)
    output_path = os.path.join(input_path, output_subdir)
    makedirs_exist_ok(output_path)
    jpg_filenames = [p for p in os.listdir(input_path) if p.endswith('.jpg')]
    dt_filename = os.path.join(input_path, 'delta_t.pck')
    delta_t = pickle.load(open(dt_filename))
    num_files = len(jpg_filenames)
    for frame, filename in enumerate(sorted(jpg_filenames)):
        if frame % (num_files / 10) == 0:
            log('image processing - %d%%' % (frame * 100 / num_files))
        sys.stdout.flush()
        image_in = Image.open(os.path.join(input_path, filename))
        (w, h) = image_in.size
        crop_box = (w/2-CROP_2, h/2-CROP_2, w/2+CROP_2, h/2+CROP_2)
        image_out = image_in.crop(crop_box).resize(OUTPUT_DIMS, Image.BILINEAR)
        draw = ImageDraw.Draw(image_out)
        dt_minutes = delta_t[frame] / 60
        ts_hours, ts_minutes = divmod(dt_minutes, 60)
        timestamp_text = '%02d:%02d (t=%d)' % (ts_hours, ts_minutes, dt_minutes)
        draw.text((10, 10), timestamp_text, font=font)
        output_frame_filename = os.path.join(output_path, filename)
        image_out.save(output_frame_filename, quality=95)
    log('image processing - 100%')
    log('rendering movie')
    temp_movie_filename = os.path.join(output_path, 'movie-temp.mp4')
    output_movie_filename = os.path.join(output_path, 'movie.mp4')
    render_command = (render_command_template %
                      (output_path, temp_movie_filename)).split(' ')
    faststart_command = (faststart_command_template %
                         (temp_movie_filename, output_movie_filename)).split(' ')
    subprocess.check_call(render_command,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    subprocess.check_call(faststart_command,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    os.unlink(temp_movie_filename)
    log('<<< END')


def render_well(well_dir):
    render_well_worker((well_dir, None))


def makedirs_exist_ok(name):
    try:
        os.makedirs(name)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
