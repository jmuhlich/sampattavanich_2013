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
SCALE_BAR_LENGTH_MICRONS = 50
SCALE_BAR_HEIGHT_PIXELS = 3

# Scale is hard-coded since metadata in OMERO is wrong (per discussion with Pat
# on 2013/12/04).
MICRONS_PER_PIXEL = 0.6450

# Limit workers since this is more disk I/O limited.
MAX_PROCESSES = 4

input_base = 'frames'
output_subdir = 'render'

font_name = 'LiberationSans-Regular.ttf'
font_timestamp = ImageFont.truetype(font_name, 24)
font_scale = ImageFont.truetype(font_name, 18)

render_command_template = (
    'ffmpeg -i %s/%%03d.jpg '
    '-y -vcodec libx264 -pix_fmt yuv420p -crf 22 -an '
    '%s'
    )
faststart_command_template ='qt-faststart %s %s'


def main(argv):
    global pool, well_dirs, map_args, result
    processes = min(multiprocessing.cpu_count(), MAX_PROCESSES)
    pool = multiprocessing.Pool(processes)
    manager = multiprocessing.Manager()
    queue = manager.Queue()
    well_dirs = os.listdir(input_base)
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
            sys.stdout.flush()
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
        image_in = Image.open(os.path.join(input_path, filename))
        (w, h) = image_in.size
        crop_box = (w/2-CROP_2, h/2-CROP_2, w/2+CROP_2, h/2+CROP_2)
        image_out = image_in.crop(crop_box).resize(OUTPUT_DIMS, Image.BILINEAR)
        draw = ImageDraw.Draw(image_out)
        dt_minutes = delta_t[frame] / 60
        ts_hours, ts_minutes = divmod(dt_minutes, 60)
        timestamp_text = '%02d:%02d (t=%d)' % (ts_hours, ts_minutes, dt_minutes)
        draw.text((10, 10), timestamp_text, font=font_timestamp)
        scale_bar_length_pixels = SCALE_BAR_LENGTH_MICRONS / MICRONS_PER_PIXEL
        scale_bar_coords = [(10, OUTPUT_DIMS[1]-10),
                            (10 + scale_bar_length_pixels,
                             OUTPUT_DIMS[1]-10-SCALE_BAR_HEIGHT_PIXELS)]
        draw.rectangle(scale_bar_coords, fill='#ffffff')
        scale_text = u"%d\xb5m" % SCALE_BAR_LENGTH_MICRONS
        scale_text_dims = draw.textsize(scale_text, font=font_scale)
        scale_text_left = (10 + scale_bar_length_pixels / 2 -
                           scale_text_dims[0] / 2)
        scale_text_top = (scale_bar_coords[1][1] - 5 -
                          sum(font_scale.getmetrics()))
        draw.text((scale_text_left, scale_text_top), scale_text, font=font_scale)
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
