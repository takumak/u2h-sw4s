#!/usr/bin/python

#  A management tool for U2H-SW4S
#  (make sure this is a little old code, written in 2012)
#
#  U2H-SW4S:
#    http://www2.elecom.co.jp/cable/usb-hub/u2h-sw4s/
#
#  See also:
#    http://www.iteclub.net/wordpress/2011/08/12/u2h-sw4x_control_software/
#    http://octais.blogspot.jp/2012/04/usb.html

import sys, os
import optparse
import select

class OptionParser(optparse.OptionParser):
  def __init__(self):
    optparse.OptionParser.__init__(self)
    self.add_option('--device', default = '/dev/u2h-sw4s',
                    help = 'HID device filename. (e.g. /dev/hidraw0)')
    self.add_option('--port', type = int,
                    help = 'Port number to activate or inactivate.')
    self.add_option('--on', action = 'store_true', dest = 'activate',
                    help = 'Activate the port specified by --port.')
    self.add_option('--off', action = 'store_false', dest = 'activate',
                    help = 'Inactivate the port specified by --port.')
    self.add_option('--quiet', action = 'store_true', default = False,
                    help = 'Suppress log output.')

def set_status(devfilename, port, activate):
  fp = open(devfilename, 'wb')
  try:
    data = b'\x00\x03\x5d\x00'
    data += bytes([[5, 2, 3, 4][port - 1], 1 if activate else 0])
    data += b'\x00\x00\x00'
    fp.write(data)
  finally:
    fp.close()

def get_status(devfilename):
  fd = os.open(devfilename, os.O_RDWR | os.O_NONBLOCK)
  request = b'\x03\x5d\x02\x00\x00\x00\x00\x00'
  os.write(fd, request)
  rlist, wlist, xlist = select.select([fd], [], [], 4)

  if not rlist:
    raise RuntimeError('Timeout')

  response = os.read(fd, 9)

  if len(response) != 8:
    raise RuntimeError('Invalid response length')

  if response[:2] != request[:2]:
    raise RuntimeError('Invalid response header')

  flags = response[2]
  if (flags & 0xc3) != 3:
    raise RuntimeError('Invalid response flags pattern - %s' % bin(flags))

  if response[3:] != b'\x00\x75\x00\x00\x00':
    raise RuntimeError('Invalid response footer - %s' % response[3:].encode('hex'))

  return tuple(map(lambda p: ((flags) & (1 << p)) > 0, [5, 2, 3, 4]))

def main(args):
  opts, args = OptionParser().parse_args(args)

  if opts.port is not None and (opts.port < 1 or opts.port > 4):
    raise RuntimeError('Invalid port number - %d' % opts.port)

  if opts.port and opts.activate is not None:
    set_status(opts.device, opts.port, opts.activate)

  flags = get_status(opts.device)

  if opts.port and opts.activate is None:
    active = flags[opts.port - 1]
    if not opts.quiet:
      print('port%d: %s' % (opts.port, 'on' if active else 'off'))
    sys.exit(0 if active else 1)

  if not opts.quiet:
    print('Device: %s' % opts.device)
    for i, flag in enumerate(flags):
      print('  port%d: %s%s' % (i + 1, 'on' if flag else 'off', ' *' if i + 1 == opts.port else ''))

if __name__ == '__main__':
  main(sys.argv)
