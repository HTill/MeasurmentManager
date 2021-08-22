from weakref import ProxyTypes
import soundcard as sc
from abc import ABC, abstractmethod
import threading
import numpy

class DeviceGroupManager():

    def __init__(self) -> None:
        self.device_group_dic = {}

    def add_device_group(self,device_group):
        self.device_group_dic.update({device_group.name:device_group})

    def process_audio_dic(self,audio_dic):
        
        threads = list()

        for audio_type,audio_block in audio_dic.items():
            for device_group in self.device_group_dic.values():

                if audio_type == device_group.audio_type:

                    x = AudioThread(device_group,audio_block)

                    threads.append(x)
                    x.start()
        
        for thread in threads:
            thread.join()

        return audio_dic
        

class AudioThread(threading.Thread):

    def __init__(self,device_group, audio_block):
        threading.Thread.__init__(self)
        self.device_group = device_group
        self.audio_block = audio_block

    def run(self):
        
        self.device_group.process_block(self.audio_block)

class DeviceGroup(ABC):

    def __init__(self,name,audio_type) -> None:
        self._name = name
        self._audio_type = audio_type
        self.device_dic = {}
        
    def add_device(self,device):
        self.device_dic.update({device.id:device})

    @abstractmethod
    def process_block(self,audio_block):
        ...

    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self,name):
        self._name = name

    @property
    def audio_type(self):
        return self._audio_type

    @audio_type.setter
    def audio_type(self,audiotype):
        self._audio_type = audiotype


class InDeviceGroup(DeviceGroup):

    def process_block(self, record_zeros):
        threads = list()

        for _,device in self.device_dic.items():
            x = AudioInThread(device,record_zeros)
            threads.append(x)
            x.start()

        for thread in threads:
            thread.join()

class OutDeviceGroup(DeviceGroup):

    def process_block(self,audio_block):
        threads = list()

        for _,device in self.device_dic.items():
            x = AudioOutThread(device,audio_block)
            threads.append(x)
            x.start()

        for thread in threads:
            thread.join()

class AudioInThread(threading.Thread):

    def __init__(self,device, record_zeros):
        threading.Thread.__init__(self)
        self._return = None
        self.device = device
        self.record_zeros = record_zeros

    def run(self):
        recording = self.device.soundcard_obj.record(numframes = self.record_zeros.shape[0],
                                                     samplerate = self.device.settings['samplerate'],
                                                     channels = self.device.settings['channels'],
                                                     blocksize = self.device.settings['blocksize'])

        self.record_zeros[0:] = recording

class AudioOutThread(threading.Thread):

    def __init__(self,device, audio_block):
        threading.Thread.__init__(self)
        self.device = device
        self.audio_block = audio_block

    def run(self):
        
        self.device.soundcard_obj.play(data = self.audio_block,
                                       samplerate = self.device.settings['samplerate'],
                                       channels = self.device.settings['channels'],
                                       blocksize = self.device.settings['blocksize'])


class Device():

    def __init__(self,soundcard_obj,settings) -> None:
        self.soundcard_obj = soundcard_obj
        self.id = soundcard_obj.id
        self._settings = settings

    @property
    def settings(self):
        return self._settings

    @settings.setter
    def settings(self,settings):
        self._settings = settings

if __name__ == '__main__':

    speaker_list = sc.all_speakers()
    print(speaker_list)
    mic_list = sc.all_microphones()
    print(mic_list)

    settings = {'channels': [0,1],
                'samplerate': 44100,
                'blocksize':512}

    speaker_device = Device(speaker_list[1],settings)
    laptopspeaker_device = Device(speaker_list[2],settings)

    mic_device = Device(mic_list[2],settings)

    noise_device_group = OutDeviceGroup('noise','noise')
    noise_device_group.add_device(speaker_device)
    noise_device_group.add_device(laptopspeaker_device)

    record_device_group = InDeviceGroup('mic','recording')
    record_device_group.add_device(mic_device)

    mm = DeviceGroupManager()
    mm.add_device_group(noise_device_group)
    mm.add_device_group(record_device_group)

    test_audio = numpy.random.randn(100000,2) * 0.001

    record_zeros = numpy.zeros(test_audio.shape)

    audio_dic = {'noise': test_audio,
                 'recording':record_zeros}

    for nn in range(2):
        mm.process_audio_dic(audio_dic)

    mm.process_audio_dic({'noise':record_zeros*100})


