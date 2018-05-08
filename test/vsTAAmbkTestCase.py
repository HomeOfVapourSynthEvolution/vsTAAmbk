import unittest
import functools
import vapoursynth as vs
import vsTAAmbk as taa


class AATestCase(unittest.TestCase):
    core = vs.get_core()
    gray8 = core.std.BlankClip(width=1920, height=1080, format=vs.GRAY8, fpsnum=24000, fpsden=1001)
    gray16 = core.std.BlankClip(width=1920, height=1080, format=vs.GRAY16, fpsnum=24000, fpsden=1001)

    aa_kernel = {
        'Dummy': lambda clip, *args, **kwargs: type('', (), {'out': lambda: clip}),
        'Eedi2': taa.AAEedi2,
        'Eedi3': taa.AAEedi3,
        'Nnedi3': taa.AANnedi3,
        'Nnedi3UpscaleSangNom': taa.AANnedi3UpscaleSangNom,
        'Spline64NrSangNom': taa.AASpline64NRSangNom,
        'Spline64SangNom': taa.AASpline64SangNom,
        'Eedi2SangNom': taa.AAEedi2SangNom,
        'Eedi3SangNom': taa.AAEedi3SangNom,
        'Nnedi3SangNom': taa.AANnedi3SangNom,
        'PointSangNom': taa.AAPointSangNom,
    }

    def test_normal_input(self):
        test_clip = [self.gray8, self.gray16]
        for clip in test_clip:
            for key in self.aa_kernel:
                aa = self.aa_kernel[key](clip, 0).out()
                self.assertTrue(isinstance(aa, vs.VideoNode))
                self.assertEqual(aa.width, clip.width)
                self.assertEqual(aa.height, clip.height)
                self.assertEqual(aa.format.bits_per_sample, clip.format.bits_per_sample)
                message = '{kernel} {depth} bit normal input test passed'
                message = message.format(kernel=key, depth=clip.format.bits_per_sample)
                print(message)

    def test_predown(self):
        test_clip = [self.gray8, self.gray16]
        strengths = [0.1, 0.4, 0.5, 0, 5.0, -1.0]
        for clip in test_clip:
            for strength in strengths:
                for key in self.aa_kernel:
                    aa = self.aa_kernel[key](clip, strength).out()
                    self.assertTrue(isinstance(aa, vs.VideoNode))
                    self.assertEqual(aa.width, clip.width)
                    self.assertEqual(aa.height, clip.height)
                    self.assertEqual(aa.format.bits_per_sample, clip.format.bits_per_sample)
                    message = '{kernel} {depth} bit {strength} strength predown test passed'
                    message = message.format(kernel=key, depth=clip.format.bits_per_sample, strength=strength)
                    print(message)

    def test_down8(self):
        test_clip = [self.gray8, self.gray16]
        for clip in test_clip:
            for key in self.aa_kernel:
                aa = self.aa_kernel[key](clip, 0, True).out()
                self.assertTrue(isinstance(aa, vs.VideoNode))
                self.assertEqual(aa.width, clip.width)
                self.assertEqual(aa.height, clip.height)
                self.assertEqual(aa.format.bits_per_sample, clip.format.bits_per_sample)
                message = '{kernel} {depth} bit down8 test passed'
                message = message.format(kernel=key, depth=clip.format.bits_per_sample)
                print(message)

    def test_opencl(self):
        test_clip = [self.gray8, self.gray16]
        for clip in test_clip:
            for key in self.aa_kernel:
                aa = self.aa_kernel[key](clip, 0, False, opencl=True).out()
                self.assertTrue(isinstance(aa, vs.VideoNode))
                self.assertEqual(aa.width, clip.width)
                self.assertEqual(aa.height, clip.height)
                self.assertEqual(aa.format.bits_per_sample, clip.format.bits_per_sample)
                message = '{kernel} {depth} bit opencl test passed'
                message = message.format(kernel=key, depth=clip.format.bits_per_sample)
                print(message)


class GeneralTestCase(unittest.TestCase):
    core = vs.get_core()
    gray8 = core.std.BlankClip(width=1920, height=1080, format=vs.GRAY8, fpsnum=24000, fpsden=1001)
    yuv420p8 = core.std.BlankClip(width=1920, height=1080, format=vs.YUV420P8, fpsnum=24000, fpsden=1001)
    yuv444p8 = core.std.BlankClip(width=1920, height=1080, format=vs.YUV444P8, fpsnum=24000, fpsden=1001)
    gray16 = core.std.BlankClip(width=1920, height=1080, format=vs.GRAY16, fpsnum=24000, fpsden=1001)
    yuv420p16 = core.std.BlankClip(width=1920, height=1080, format=vs.YUV420P16, fpsnum=24000, fpsden=1001)
    yuv444p16 = core.std.BlankClip(width=1920, height=1080, format=vs.YUV444P16, fpsnum=24000, fpsden=1001)
    format_id = {
        '1000010': 'GRAY8',
        '1000011': 'GRAY16',
        '3000010': 'YUV420P8',
        '3000012': 'YUV444P8',
        '3000022': 'YUV420P16',
        '3000024': 'YUV444P16',
    }

    def test_default_value(self):
        test_clips = [self.gray8, self.yuv420p8, self.yuv444p8, self.gray16, self.yuv420p16, self.yuv444p16]
        for clip in test_clips:
            aa = taa.TAAmbk(clip)
            self.assertTrue(isinstance(aa, vs.VideoNode))
            self.assertEqual(aa.width, clip.width)
            self.assertEqual(aa.height, clip.height)
            self.assertEqual(aa.format.bits_per_sample, clip.format.bits_per_sample)
            message = 'default value test: {}bit {} format test passed'
            message = message.format(clip.format.bits_per_sample, self.format_id[str(clip.format.id)])
            print(message)

    def test_aatype(self):
        aatypes = [0, 1, 2, 3, 4, 5, 6, -1, -2, -3, 'Nnedi3', 'Nnedi3SangNom', 'Nnedi3UpscaleSangNom', 'Eedi2',
                   'Eedi2SangNom', 'Eedi3', 'Eedi3SangNom', 'PointSangNom', 'Spline64SangNom', 'Spline64NrSangNom']
        test_clips = [self.gray8, self.yuv420p8, self.yuv444p8, self.gray16, self.yuv420p16, self.yuv444p16]
        for clip in test_clips:
            for aatype in aatypes:
                aa = taa.TAAmbk(clip, aatype=aatype)
                self.assertTrue(isinstance(aa, vs.VideoNode))
                self.assertEqual(aa.width, clip.width)
                self.assertEqual(aa.height, clip.height)
                self.assertEqual(aa.format.bits_per_sample, clip.format.bits_per_sample)
                message = 'aatype {}: {}bit {} format test passed'
                message = message.format(aatype, clip.format.bits_per_sample, self.format_id[str(clip.format.id)])
                print(message)
        with self.assertRaises(ValueError):
            aa = taa.TAAmbk(test_clips[1], aatype='DoNotExist')
        print('aatype negative test passed')

    def test_custom_aatype(self):
        test_clips = [self.gray8, self.yuv420p8, self.yuv444p8, self.gray16, self.yuv420p16, self.yuv444p16]
        my_aa_kernel = type('', (taa.AANnedi3,), {'out': lambda self: self.output(self.aa_clip)})
        for clip in test_clips:
            aa = taa.TAAmbk(clip, aatype='Custom', aatypeu='Custom', aatypev='Nnedi3', aakernel=my_aa_kernel)
            self.assertTrue(isinstance(aa, vs.VideoNode))
            self.assertEqual(aa.width, clip.width)
            self.assertEqual(aa.height, clip.height)
            self.assertEqual(aa.format.bits_per_sample, clip.format.bits_per_sample)
            with self.assertRaises(RuntimeError):
                aa2 = taa.TAAmbk(clip, aatype='Custom', aatypeu=1, aatypev=1)
            message = 'custom aatype: {}bit {} format test passed'
            message = message.format(clip.format.bits_per_sample, self.format_id[str(clip.format.id)])
            print(message)

    @unittest.skip('aatype sepeated test cost too much time. Run as needed.')
    def test_aatype_seperate(self):
        aatypes = ['Nnedi3', 'Nnedi3SangNom', 'Nnedi3UpscaleSangNom', 'Eedi2', 'Eedi2SangNom', 'Eedi3', 'Eedi3SangNom',
                   'PointSangNom', 'Spline64SangNom', 'Spline64NrSangNom']
        test_clips = [self.yuv420p8, self.yuv444p8, self.yuv420p16, self.yuv444p16]
        for clip in test_clips:
            for aatype_y in aatypes:
                for aatype_u in aatypes:
                    for aatype_v in aatypes:
                        aa = taa.TAAmbk(clip, aatype=aatype_y, aatypeu=aatype_u, aatypev=aatype_v)
                        self.assertTrue(isinstance(aa, vs.VideoNode))
                        self.assertEqual(aa.width, clip.width)
                        self.assertEqual(aa.height, clip.height)
                        self.assertEqual(aa.format.bits_per_sample, clip.format.bits_per_sample)
                        message = 'aatype {}. aatypeu {}, aatypev {}: {}bit {} format test passed'
                        message = message.format(aatype_y, aatype_u, aatype_v, clip.format.bits_per_sample,
                                                 self.format_id[str(clip.format.id)])
                        print(message)

    def test_preaa(self):
        test_clips = [self.gray8, self.yuv420p8, self.yuv444p8, self.gray16, self.yuv420p16, self.yuv444p16]
        preaa_types = [-1, 0, 1, 2]
        for clip in test_clips:
            for preaa_type in preaa_types:
                preaa_with_main_aa = taa.TAAmbk(clip, aatype=0, preaa=preaa_type)
                preaa_without_main_aa = taa.TAAmbk(clip, aatype=1, preaa=preaa_type)
                self.assertTrue(isinstance(preaa_with_main_aa, vs.VideoNode))
                self.assertEqual(preaa_with_main_aa.width, clip.width)
                self.assertEqual(preaa_with_main_aa.height, clip.height)
                self.assertEqual(preaa_with_main_aa.format.bits_per_sample, clip.format.bits_per_sample)
                self.assertTrue(isinstance(preaa_without_main_aa, vs.VideoNode))
                self.assertEqual(preaa_without_main_aa.width, clip.width)
                self.assertEqual(preaa_without_main_aa.height, clip.height)
                self.assertEqual(preaa_without_main_aa.format.bits_per_sample, clip.format.bits_per_sample)
                message = 'preaa {}: {}bit {} format test passed'
                message = message.format(str(preaa_type), clip.format.bits_per_sample,
                                         self.format_id[str(clip.format.id)])
                print(message)

    def test_predown(self):
        test_clips = [self.gray8, self.yuv420p8, self.yuv444p8, self.gray16, self.yuv420p16, self.yuv444p16]
        strengths = [i / 10 for i in range(6)]
        for clip in test_clips:
            for strength in strengths:
                aa = taa.TAAmbk(clip, aatype=-1, aatypeu=3, aatypev=0, strength=strength)
                self.assertTrue(isinstance(aa, vs.VideoNode))
                self.assertEqual(aa.width, clip.width)
                self.assertEqual(aa.height, clip.height)
                self.assertEqual(aa.format.bits_per_sample, clip.format.bits_per_sample)
                message = 'predown strength {}: {}bit {} format test passed'
                message = message.format(str(strength), clip.format.bits_per_sample,
                                         self.format_id[str(clip.format.id)])
                print(message)

    def test_cycle(self):
        test_clips = [self.gray8, self.yuv420p8, self.yuv444p8, self.gray16, self.yuv420p16, self.yuv444p16]
        cycles = [i for i in range(6)]
        for clip in test_clips:
            for cycle in cycles:
                aa = taa.TAAmbk(clip, aatype=1, strength=0.3, cycle=cycle)
                self.assertTrue(isinstance(aa, vs.VideoNode))
                self.assertEqual(aa.width, clip.width)
                self.assertEqual(aa.height, clip.height)
                self.assertEqual(aa.format.bits_per_sample, clip.format.bits_per_sample)
                message = 'cycle {}: {}bit {} format test passed'
                message = message.format(str(cycle), clip.format.bits_per_sample,
                                         self.format_id[str(clip.format.id)])
                print(message)

    def test_mtype(self):
        test_clips = [self.gray8, self.yuv420p8, self.yuv444p8, self.gray16, self.yuv420p16, self.yuv444p16]
        mtypes = [0, 1, 2, 3, 4, 5, 6, 'Canny', 'Sobel', 'Prewitt', 'Canny_Old', 'Robert', 'MSharpen', 'TEdge']
        for clip in test_clips:
            for mtype in mtypes:
                aa = taa.TAAmbk(clip, aatype=1, mtype=mtype)
                self.assertTrue(isinstance(aa, vs.VideoNode))
                self.assertEqual(aa.width, clip.width)
                self.assertEqual(aa.height, clip.height)
                self.assertEqual(aa.format.bits_per_sample, clip.format.bits_per_sample)
                message = 'mtype {}: {}bit {} format test passed'
                message = message.format(str(mtype), clip.format.bits_per_sample,
                                         self.format_id[str(clip.format.id)])
                print(message)
        with self.assertRaises(ValueError):
            aa = taa.TAAmbk(test_clips[1], aatype=1, mtype='DoNotExist')
        print('mtype: negative test passed')

    def test_mthr(self):
        test_clips = [self.gray8, self.yuv420p8, self.yuv444p8, self.gray16, self.yuv420p16, self.yuv444p16]
        mtypes = ['Canny', 'Sobel', 'Prewitt', 'Canny_Old', 'Robert', 'MSharpen', 'TEdge']
        mthrs = range(1, 255, 15)
        for clip in test_clips:
            for mtype in mtypes:
                for mthr in mthrs:
                    aa = taa.TAAmbk(clip, aatype=1, mtype=mtype, mthr=mthr)
                    self.assertTrue(isinstance(aa, vs.VideoNode))
                    self.assertEqual(aa.width, clip.width)
                    self.assertEqual(aa.height, clip.height)
                    self.assertEqual(aa.format.bits_per_sample, clip.format.bits_per_sample)
                    message = 'mtype {} mthr {}: {}bit {} format test passed'
                    message = message.format(str(mtype), str(mthr), clip.format.bits_per_sample,
                                             self.format_id[str(clip.format.id)])
                    print(message)

    def test_mpand(self):
        test_clips = [self.gray8, self.yuv420p8, self.yuv444p8, self.gray16, self.yuv420p16, self.yuv444p16]
        mpands = [0, (0, 1), (1, 0), (2, 2), [2, 1]]
        for clip in test_clips:
            for mpand in mpands:
                aa = taa.TAAmbk(clip, aatype=1, mtype=3, mthr=[24, 46], mlthresh=59, mpand=mpand)
                self.assertTrue(isinstance(aa, vs.VideoNode))
                self.assertEqual(aa.width, clip.width)
                self.assertEqual(aa.height, clip.height)
                self.assertEqual(aa.format.bits_per_sample, clip.format.bits_per_sample)
                message = 'mpand {}: {}bit {} format test passed'
                message = message.format(str(mpand), clip.format.bits_per_sample,
                                         self.format_id[str(clip.format.id)])
                print(message)

    def test_txtmask(self):
        test_clips = [self.gray8, self.yuv420p8, self.yuv444p8, self.gray16, self.yuv420p16, self.yuv444p16]
        txtmasks = [0, 255, 128]
        txtfades = [0, 3, (3, 0), [0, 5], [2, 3]]
        for clip in test_clips:
            for txtmask in txtmasks:
                for txtfade in txtfades:
                    aa = taa.TAAmbk(clip, aatype=1, mtype=1, txtmask=txtmask, txtfade=txtfade)
                    self.assertTrue(isinstance(aa, vs.VideoNode))
                    self.assertEqual(aa.width, clip.width)
                    self.assertEqual(aa.height, clip.height)
                    self.assertEqual(aa.format.bits_per_sample, clip.format.bits_per_sample)
                    message = 'txtmask {} txtfade {}: {}bit {} format test passed'
                    message = message.format(str(txtmask), str(txtfade), clip.format.bits_per_sample,
                                             self.format_id[str(clip.format.id)])
                    print(message)

    def test_preprocess(self):
        test_clips = [self.gray8, self.yuv420p8, self.yuv444p8, self.gray16, self.yuv420p16, self.yuv444p16]
        for clip in test_clips:
            aa = taa.TAAmbk(clip, aatype=1, mtype=1, dark=8.0, thin=4)
            self.assertTrue(isinstance(aa, vs.VideoNode))
            self.assertEqual(aa.width, clip.width)
            self.assertEqual(aa.height, clip.height)
            self.assertEqual(aa.format.bits_per_sample, clip.format.bits_per_sample)
            message = 'thin and dark: {}bit {} format test passed'
            message = message.format(clip.format.bits_per_sample, self.format_id[str(clip.format.id)])
            print(message)

    def test_aarepair(self):
        test_clips = [self.gray8, self.yuv420p8, self.yuv444p8, self.gray16, self.yuv420p16, self.yuv444p16]
        repairs = [-i for i in range(25)] + [i for i in range(25)]
        for clip in test_clips:
            for repair in repairs:
                aa = taa.TAAmbk(clip, aatype=1, mtype=1, aarepair=repair, sharp=-1)
                self.assertTrue(isinstance(aa, vs.VideoNode))
                self.assertEqual(aa.width, clip.width)
                self.assertEqual(aa.height, clip.height)
                self.assertEqual(aa.format.bits_per_sample, clip.format.bits_per_sample)
                message = 'aarepair {}: {}bit {} format test passed'
                message = message.format(str(repair), clip.format.bits_per_sample, self.format_id[str(clip.format.id)])
                print(message)

    def test_sharp(self):
        test_clips = [self.gray8, self.yuv420p8, self.yuv444p8, self.gray16, self.yuv420p16, self.yuv444p16]
        sharps = [0, 30, 0.6, -0.08, -1]
        for clip in test_clips:
            for sharp in sharps:
                aa = taa.TAAmbk(clip, aatype=1, mtype=3, preaa=-1, sharp=sharp)
                self.assertTrue(isinstance(aa, vs.VideoNode))
                self.assertEqual(aa.width, clip.width)
                self.assertEqual(aa.height, clip.height)
                self.assertEqual(aa.format.bits_per_sample, clip.format.bits_per_sample)
                message = 'sharp {}: {}bit {} format test passed'
                message = message.format(str(sharp), clip.format.bits_per_sample, self.format_id[str(clip.format.id)])
                print(message)

    def test_postaa(self):
        test_clips = [self.gray8, self.yuv420p8, self.yuv444p8, self.gray16, self.yuv420p16, self.yuv444p16]
        for clip in test_clips:
            aa = taa.TAAmbk(clip, aatype=1, mtype=3, preaa=-1, sharp=-1, postaa=True)
            self.assertTrue(isinstance(aa, vs.VideoNode))
            self.assertEqual(aa.width, clip.width)
            self.assertEqual(aa.height, clip.height)
            self.assertEqual(aa.format.bits_per_sample, clip.format.bits_per_sample)
            message = 'postaa: {}bit {} format test passed'
            message = message.format(clip.format.bits_per_sample, self.format_id[str(clip.format.id)])
            print(message)

    def test_stabilize(self):
        test_clips = [self.gray8, self.yuv420p8, self.yuv444p8, self.gray16, self.yuv420p16, self.yuv444p16]
        stabilizes = [i for i in range(4)]
        for clip in test_clips:
            for stabilize in stabilizes:
                aa = taa.TAAmbk(clip, aatype=1, mtype=3, preaa=-1, sharp=-1, postaa=True, stabilize=stabilize)
                self.assertTrue(isinstance(aa, vs.VideoNode))
                self.assertEqual(aa.width, clip.width)
                self.assertEqual(aa.height, clip.height)
                self.assertEqual(aa.format.bits_per_sample, clip.format.bits_per_sample)
                message = 'stabilize {}: {}bit {} format test passed'
                message = message.format(str(stabilize), clip.format.bits_per_sample,
                                         self.format_id[str(clip.format.id)])
                print(message)

    def test_src(self):
        test_clips = [self.gray8, self.yuv420p8, self.yuv444p8, self.gray16, self.yuv420p16, self.yuv444p16]
        src_clips = list(test_clips)
        for clip, src in zip(test_clips, src_clips):
            aa = taa.TAAmbk(clip, aatype=1, mtype=3, sharp=-1, src=src)
            self.assertTrue(isinstance(aa, vs.VideoNode))
            self.assertEqual(aa.width, clip.width)
            self.assertEqual(aa.height, clip.height)
            self.assertEqual(aa.format.bits_per_sample, clip.format.bits_per_sample)
            message = 'src clip: {}bit {} format test passed'
            message = message.format(clip.format.bits_per_sample, self.format_id[str(clip.format.id)])
            print(message)
        with self.assertRaises(ValueError):
            aa2 = taa.TAAmbk(self.gray16, aatype=1, mtype=2, src=self.gray8)
        print('src clip: negative test passed')

    def test_showmask(self):
        test_clips = [self.yuv420p8, self.yuv444p8, self.yuv420p16, self.yuv444p16]
        showmasks = [-1, 0, 1, 2, 3]
        for clip in test_clips:
            for mtype in [0, 1]:
                aa_func = functools.partial(taa.TAAmbk, aatype=1, mtype=mtype, txtmask=225, txtfade=3)
                for showmask in showmasks:
                    aa = aa_func(clip=clip, showmask=showmask)
                    self.assertTrue(isinstance(aa, vs.VideoNode))
                    self.assertEqual(aa.format.bits_per_sample, clip.format.bits_per_sample)
                    message = 'showmask {}: {}bit {} format test passed'
                    message = message.format(str(showmask), clip.format.bits_per_sample,
                                             self.format_id[str(clip.format.id)])
                    print(message)


if __name__ == '__main__':
    unittest.main()
