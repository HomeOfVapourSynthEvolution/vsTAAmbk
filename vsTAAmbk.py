##==========================================================
## 2016.02.09			vsTAAmbk 0.6.0					
##			Ported from TAAmbk 0.7.0 by Evalyn
##          Maintained by Evalyn pov@mahou-shoujo.moe		
##			              kewenyu 1059902659@qq.com		
##==========================================================
##			Requirements:								
##						EEDI2							
##						nnedi3							
##						RemoveGrain/Repair				
##						fmtconv							
##						GenericFilters					
##						MSmoosh							
##						MVTools							
##						TemporalSoften					
##						sangnom							
##						HAvsFunc(and its requirements)	
##			VapourSynth R28 or newer
##
##==========================================================
##==========================================================
##														
##	#### Only YUV colorfmaily is supported ! 	
##	#### And input bitdepth must be 8 or 16 INT !			
##		 												
##==========================================================	 												







import vapoursynth as vs
import havsfunc as haf
import mvsfunc as mvf

def TAAmbkX(input, aatype=1, strength=0.0, preaa=0, cycle=0,
           mtype=None, mclip=None, mthr=None, mthr2=None, mlthresh=None, mpand=[2,1], txtprt=None,
           thin=0, dark=0.0,
           sharp=0, repair=0, postaa=None, src=None, stabilize=0,
           down8=False, showmask=0, **pn):
    
    
    core = vs.get_core()
    
    
    # Constant Values
    FUNCNAME = 'TAAmbkX'    # 'X' refer to 'Experimental'. Will change to vsTAAmbk when it is stable
    W = input.width
    H = input.height
    BPS = input.format.bits_per_sample
    COLOR_FAMILY = input.format.color_family
    SAMPLE_TYPE = input.format.sample_type
    ID = input.format.id
    SUBSAMPLE = input.format.subsampling_h
    IS_GRAY = True if input.format.num_planes == 1 else False
    ABS_SHARP = abs(sharp)
    STR = strength    # Strength of predown
    PROCE_DEPTH = BPS if down8 == False else 8    # Process bitdepth
    
    
    # Associated Default Values
    if mtype is None:
        mtype = 0 if preaa == 0 and aatype == 0 else 1
    if postaa is None:
        postaa = True if ABS_SHARP > 70 or (ABS_SHARP > 0.4 and ABS_SHARP < 1) else False
    
        
    if src is None:
        src = input
    else:
        if src.format.id != ID or src.width != W or src.height != H:
            raise RuntimeError(FUNCNAME + ': src format and input mismatch !')
    
    
    # Input Check
    if not isinstance(input, vs.VideoNode):
        raise ValueError(FUNCNAME + ': input must be a clip !')
    if COLOR_FAMILY == vs.YUV or COLOR_FAMILY == vs.GRAY:
        if SAMPLE_TYPE != vs.INTEGER:
            raise TypeError(FUNCNAME + ': input must be integer format !')
        if not (BPS == 8 or BPS == 16):
            raise TypeError(FUNCNAME + ': input must be 8bit or 16bit !')
    else:
        raise TypeError(FUNCNAME + ': input must be YUV or GRAY !')        
        
    
############### Internal Functions ###################
    def Preaa(input, mode):
         nn = None if mode == 2 else core.nnedi3.nnedi3(input, field=3)
         nnt = None if mode == 1 else core.nnedi3.nnedi3(core.std.Transpose(input), field=3).std.Transpose()
         clph = None if mode == 2 else core.std.Merge(core.std.SelectEvery(nn, cycle=2, offsets=0), core.std.SelectEvery(nn, cycle=2, offsets=1))
         clpv = None if mode == 1 else core.std.Merge(core.std.SelectEvery(nnt, cycle=2, offsets=0), core.std.SelectEvery(nnt, cycle=2, offsets=1))
         clp = core.std.Merge(clph, clpv) if mode == -1 else None
         if mode == 1:
             return clph
         elif mode == 2:
             return clpv
         else:
             return clp
    
    
    def Lineplay(input, thin, dark):
        if thin != 0 and dark != 0:
            return haf.Toon(core.warp.AWarpSharp2(input, depth=int(thin)), str=float(dark))
        elif thin == 0:
            return haf.Toon(input, str=float(dark))
        else:
            return core.warp.AWarpSharp2(input, depth=int(thin))
    
    
    def Stabilize(clip, src, delta):
        aaDiff = core.std.MakeDiff(src, input, planes=[0,1,2])
        inSuper = core.mv.Super(clip, pel=1)
        diffSuper = core.mv.Super(aaDiff, pel=1, levels=1)
        
        fv3 = core.mv.Analyse(inSuper, isb=False, delta=3, overlap=8, blksize=16) if delta == 3 else None
        fv2 = core.mv.Analyse(inSuper, isb=False, delta=2, overlap=8, blksize=16) if delta >= 2 else None
        fv1 = core.mv.Analyse(inSuper, isb=False, delta=1, overlap=8, blksize=16) if delta >= 1 else None
        bv1 = core.mv.Analyse(inSuper, isb=True, delta=1, overlap=8, blksize=16) if delta >= 1 else None
        bv2 = core.mv.Analyse(inSuper, isb=True, delta=2, overlap=8, blksize=16) if delta >= 2 else None
        bv3 = core.mv.Analyse(inSuper, isb=True, delta=3, overlap=8, blksize=16) if delta == 3 else None
        
        if stabilize == 1:
            diffStab = core.mv.Degrain1(aaDiff, diffSuper, bv1, fv1)
        elif stabilize == 2:
            diffStab = core.mv.Degrain2(aaDiff, diffSuper, bv1, fv1, bv2, fv2)
        elif stabilize == 3:
            diffStab = core.mv.Degrain3(aaDiff, diffSuper, bv1, fv1, bv2, fv2, bv3, fv3)
        else:
            raise ValueError(FUNCNAME + ': \"stabilize\" int(0~3) invaild !')
        
        # Caculate for high-bitdepth support
        neutral = 128 << (BPS - 8)
        
        compareExpr = "x {neutral} - abs y {neutral} - abs < x y ?".format(neutral=neutral)
        diffCompare = core.std.Expr([aaDiff,diffStab], compareExpr)
        diffCompare = core.std.Merge(diffCompare, diffStab, 0.6)
        
        aaStab = core.std.MakeDiff(src, diffCompare, planes=[0,1,2])
        return aaStab
    
    
    def Soothe(sharped, src):
        neutral = 128 << (BPS - 8)
        peak = (1 << BPS) - 1
        multiple = peak / 255
        const = 100 * multiple
        keep = 24
        kp = keep * multiple
        
        diff1Expr = "x y - {neutral} +".format(neutral=neutral)
        diff1 = core.std.Expr([src,sharped], diff1Expr)
        
        diff2 = core.focus.TemporalSoften(diff1, radius=1, luma_threshold=255, chroma_threshold=255, scenechange=32, mode=2)
        
        diff3Expr = "x {neutral} - y {neutral} - * 0 < x {neutral} - {const} / {kp} * {neutral} + x {neutral} - abs y {neutral} - abs > x {kp} * y {const} {kp} - * + {const} / x ? ?".format(neutral=neutral, const=const, kp=kp)
        diff3 = core.std.Expr([diff1,diff2], diff3Expr)
        
        finalExpr = "x y {neutral} - -".format(neutral=neutral)
        final = core.std.Expr([src,diff3], finalExpr)
        
        return final
    
    
    def Sharp(aaclip, aasrc, aasharp):
        if sharp >= 1:
            sharped = haf.LSFmod(aaclip, strength=int(ABS_SHARP), defaults="old", source=aasrc)
        elif sharp > 0:
            per = int(40*ABS_SHARP)
            matrix = [-1,-2,-1,-2,52 - per,-2,-1,-2,-1]
            sharped = core.std.Convolution(aaclip, matrix)
        elif sharp > -1:
            sharped = haf.LSFmod(aaclip, strength=round(ABS_SHARP*100), defaults="fast", source=aasrc)
        elif sharp == -1:
            clipb = core.std.MakeDiff(aaclip, core.rgvs.RemoveGrain(aaclip, mode=20 if W > 1100 else 11))
            clipb = core.rgvs.Repair(clipb, core.std.MakeDiff(aasrc, aaclip), mode=13)
            sharped = core.std.MergeDiff(aaclip, clipb)
        else:
            sharped = haf.LSFmod(aaclip, strength=int(ABS_SHARP), defaults="slow", source=aasrc)
            
        return sharped
        
        
        
        
######################### Begin of Main AAtype#########################    
    class aaParent:
        def __init__(self):
            self.dfactor = 1 - min(STR, 0.5)
            self.dw = round(W * self.dfactor / 4) * 4
            self.dh = round(H * self.dfactor / 4) * 4
            self.upw4 = round(self.dw * 0.375) * 4
            self.uph4 = round(self.dh * 0.375) * 4
    
        
        def aaResizer(self, clip, w, h, shift):
            resized = core.fmtc.resample(clip, w, h, sy=[shift, shift*(1 << SUBSAMPLE)])
            return mvf.Depth(resized, PROCE_DEPTH)
    
        ''' For vapoursynth R33 or greater
        def aaResizer(self, clip, w, h, shift):
            y = core.resize.Spline36(clip, width=w, height=h, src_top=shift)
            uv = core.resize.Spline36(clip, width=w, height=h, src_top=shift*(1 << SUBSAMPLE))
            return core.std.ShufflePlanes([y,uv], [0,1,2], colorfamily=vs.YUV)
        '''
    
        def aaParaInit(self, args, name, default):
            try:
                return args[name]
            except:
                return default
    
    class aaNnedi3(aaParent):
        def __init__(self, args):
            super(aaNnedi3, self).__init__()
            self.nsize = self.aaParaInit(args, 'nsize', 3)
            self.nns = self.aaParaInit(args, 'nns', 1)
            self.qual = self.aaParaInit(args, 'qual', 2)
    
        def AA(self, clip):
            aaed = core.nnedi3.nnedi3(clip, field=1, dh=True, nsize=self.nsize, nns=self.nns, qual=self.qual)
            aaed = self.aaResizer(aaed, W, H, -0.5)
            aaed = core.std.Transpose(aaed)
            aaed = core.nnedi3.nnedi3(aaed, field=1, dh=True, nsize=self.nsize, nns=self.nns, qual=self.qual)
            aaed = self.aaResizer(aaed, H, W, -0.5)
            aaed = core.std.Transpose(aaed)
            return aaed
        

    class aaNnedi3SangNom(aaNnedi3):
        def __init__(self, args):
            super(aaNnedi3SangNom, self).__init__(args)
            self.aa = self.aaParaInit(args, 'aa', 48)
        
        def AA(self, clip):
            aaed = core.nnedi3.nnedi3(clip, field=1, dh=True, nsize=self.nsize, nns=self.nns, qual=self.qual)
            aaed = self.aaResizer(aaed, W, self.uph4, -0.5)
            aaed = core.std.Transpose(aaed)
            aaed = core.nnedi3.nnedi3(aaed, field=1, dh=True, nsize=self.nsize, nns=self.nns, qual=self.qual)
            aaed = self.aaResizer(aaed, self.uph4, self.upw4, -0.5)
            aaed = core.sangnom.SangNom(aaed, aa=self.aa)
            aaed = core.std.Transpose(aaed)
            aaed = core.sangnom.SangNom(aaed, aa=self.aa)
            aaed = self.aaResizer(aaed, W, H, 0)
            return aaed


    class aaEedi3(aaParent):
        def __init__(self, args):
            super(aaEedi3, self).__init__()
            self.alpha = self.aaParaInit(args, 'alpha', 0.5)
            self.beta = self.aaParaInit(args, 'beta', 0.2)
            self.gamma = self.aaParaInit(args, 'gamma', 20)
            self.nrad = self.aaParaInit(args, 'nrad', 3)
            self.mdis = self.aaParaInit(args, 'mdis', 30)
    
        def down8(self, clip):
            if BPS == 16 and PROCE_DEPTH != 8:
                return mvf.Depth(clip, 8)
            else:
                return clip
    
        def AA(self, clip):
            aaed = core.eedi3.eedi3(self.down8(clip), field=1, dh=True, alpha=self.alpha, beta=self.beta, gamma=self.gamma, nrad=self.nrad, mdis=self.mdis)
            aaed = self.aaResizer(aaed, W, H, -0.5)
            aaed = core.std.Transpose(aaed)
            aaed = core.eedi3.eedi3(self.down8(aaed), field=1, dh=True, alpha=self.alpha, beta=self.beta, gamma=self.gamma, nrad=self.nrad, mdis=self.mdis)
            aaed = self.aaResizer(aaed, H, W, -0.5)
            aaed = core.std.Transpose(aaed)
            return mvf.Depth(aaed, PROCE_DEPTH)


    class aaEedi3SangNom(aaEedi3):
        def __init__(self, args):
            super(aaEedi3SangNom, self).__init__(args)
            self.aa = self.aaParaInit(args, 'aa', 48)
        
        def AA(self, clip):
            aaed = core.eedi3.eedi3(self.down8(clip), field=1, dh=True, alpha=self.alpha, beta=self.beta, gamma=self.gamma, nrad=self.nrad, mdis=self.mdis)
            aaed = self.aaResizer(aaed, W, self.uph4, -0.5)
            aaed = core.std.Transpose(aaed)
            aaed = core.eedi3.eedi3(self.down8(aaed), field=1, dh=True, alpha=self.alpha, beta=self.beta, gamma=self.gamma, nrad=self.nrad, mdis=self.mdis)
            aaed = self.aaResizer(aaed, self.uph4, self.upw4, -0.5)
            aaed = core.sangnom.SangNom(aaed, aa=self.aa)
            aaed = core.std.Transpose(aaed)
            aaed = core.sangnom.SangNom(aaed, aa=self.aa)
            aaed = self.aaResizer(aaed, W, H, 0)
            return mvf.Depth(aaed, PROCE_DEPTH)


    class aaEedi2(aaParent):
        def __init__(self, args):
            super(aaEedi2, self).__init__()
            self.mthresh = self.aaParaInit(args, 'mthresh', 10)
            self.lthresh = self.aaParaInit(args, 'lthresh', 20)
            self.vthresh = self.aaParaInit(args, 'vthresh', 20)
            self.maxd = self.aaParaInit(args, 'maxd', 24)
            self.nt = self.aaParaInit(args, 'nt', 50)
    
        def AA(self, clip):
            aaed = core.eedi2.EEDI2(clip, 1, self.mthresh, self.lthresh, self.vthresh, maxd=self.maxd, nt=self.nt)
            aaed = self.aaResizer(aaed, W, H, -0.5)
            aaed = core.std.Transpose(aaed)
            aaed = core.eedi2.EEDI2(aaed, 1, self.mthresh, self.lthresh, self.vthresh, maxd=self.maxd, nt=self.nt)
            aaed = self.aaResizer(aaed, H, W, -0.5)
            aaed = core.std.Transpose(aaed)
            return aaed


    class aaEedi2SangNom(aaEedi2):
        def __init__(self, args):
            super(aaEedi2SangNom, self).__init__(args)
            self.aa = self.aaParaInit(args, 'aa', 48)
        
        def AA(self, clip):
            aaed = core.eedi2.EEDI2(clip, 1, self.mthresh, self.lthresh, self.vthresh, maxd=self.maxd, nt=self.nt)
            aaed = self.aaResizer(aaed, W, self.uph4, -0.5)
            aaed = core.std.Transpose(aaed)
            aaed = core.eedi2.EEDI2(aaed, 1, self.mthresh, self.lthresh, self.vthresh, maxd=self.maxd, nt=self.nt)
            aaed = self.aaResizer(aaed, self.uph4, self.upw4, -0.5)
            aaed = core.sangnom.SangNom(aaed, aa=self.aa)
            aaed = core.std.Transpose(aaed)
            aaed = core.sangnom.SangNom(aaed, aa=self.aa)
            aaed = self.aaResizer(aaed, W, H, 0)
            return aaed


    class aaSpline64NrSangNom(aaParent):
        def __init__(self, args):
            super(aaSpline64NrSangNom, self).__init__()
            self.aa = self.aaParaInit(args, 'aa', 48)
    
        def AA(self, clip):
            aaed = core.fmtc.resample(clip, self.upw4, self.uph4, kernel="spline64")
            aaed = mvf.Depth(aaed, PROCE_DEPTH)
            aaGaussian = core.fmtc.resample(clip, self.upw4, self.uph4, kernel="gaussian", a1=100)
            aaGaussian = mvf.Depth(aaGaussian, PROCE_DEPTH)
            aaed = core.rgvs.Repair(aaed, aaGaussian, 1)
            aaed = core.sangnom.SangNom(aaed, aa=self.aa)
            aaed = core.std.Transpose(aaed)
            aaed = core.sangnom.SangNom(aaed, aa=self.aa)
            aaed = core.std.Transpose(self.aaResizer(aaed, H, W, 0))
            return aaed


    class aaSpline64SangNom(aaParent):
        def __init__(self, args):
            super(aaSpline64SangNom, self).__init__()
            self.aa = self.aaParaInit(args, 'aa', 48)
            self.mode = self.aaParaInit(args, 'mode', 0)
        
        def AA(self, clip):
            aaed = core.fmtc.resample(clip, W, self.uph4, kernel="spline64")
            aaed = mvf.Depth(aaed, PROCE_DEPTH)
            aaed = core.sangnom.SangNom(aaed, aa=self.aa)
            aaed = core.std.Transpose(self.aaResizer(aaed, W, H, 0))
            aaed = core.fmtc.resample(aaed, H, self.upw4, kernel="spline64")
            aaed = mvf.Depth(aaed, PROCE_DEPTH)
            aaed = core.sangnom.SangNom(aaed, aa=self.aa)
            aaed = core.std.Transpose(self.aaResizer(aaed, H, W, 0))
            return aaed


    class aaPointSangNom(aaParent):
        def __init__(self, args):
            super(aaPointSangNom, self).__init__()
            self.aa = self.aaParaInit(args, 'aa', 48)
            self.upw = self.dw * 2
            self.uph = self.dh * 2
    
        def AA(self, clip):
            aaed = core.resize.Point(clip, self.upw, self.uph)
            aaed = core.sangnom.SangNom(aaed, aa=self.aa)
            aaed = core.std.Transpose(aaed)
            aaed = core.sangnom.SangNom(aaed, aa=self.aa)
            aaed = self.aaResizer(core.std.Transpose(aaed), W, H, 0)
            return aaed

##################### End of Main AAType ########################


##################### Begin of Mtype ###########################

    class mParent:
        def __init__(self):
            self.outdepth = vs.GRAY8 if PROCE_DEPTH == 8 else vs.GRAY16
            self.multi = 1 if PROCE_DEPTH == 8 else 257    # Multiple factor of Expr
    
        def mParaInit(self, mthr, default):
            if mthr is not None:
                return mthr
            else:
                return default
    
        def mCheckList(self, list1, list2, list3):
            if len(list1) != (len(list2) - 1):
                raise ValueError(FUNCNAME + ': num of mthr and mlthresh mismatch !')
            if len(list2) != len(list3):
                raise ValueError(FUNCNAME + ': num of mthr and mthr2 mismatch !')
            
        def mGetGray(self, clip):
            return core.std.ShufflePlanes(clip, 0, vs.GRAY)
    
        '''
        def mBlankClip(clip):
            blc = core.std.BlankClip(clip, format=vs.GRAY8 if PROCE_DEPTH == 8 else vs.GRAY16)
            return blc 
        '''  
    
        def mExpand(self, clip, time):
            for i in range(time):
                clip = core.std.Maximum(clip, 0)
            return clip
    
        def mInpand(self, clip, time):
            for i in range(time):
                clip = core.std.Minimum(clip, 0)
            return clip
        
    class mCanny(mParent):
        def __init__(self, mthr, mthr2, mlthresh, mpand):
            super(mCanny, self).__init__()
            self.sigma = self.mParaInit(mthr, 1.2)
            self.t_h = self.mParaInit(mthr2, 8.0)
            self.mlthresh = mlthresh
            self.mpand = mpand
    
        def getMask(self, clip):
            clip = self.mGetGray(clip)
            if isinstance(self.sigma, list):
                self.mCheckList(self.mlthresh, self.sigma, self.t_h)
                mask = core.tcanny.TCanny(clip, sigma=self.sigma[0], t_h=self.t_h[0], mode=0, planes=0)
                
                for i in range(len(self.mlthresh)):
                    tmask = core.tcanny.TCanny(clip, sigma=self.sigma[i+1], t_h=self.t_h[i+1], mode=0, planes=0)
                    expr = "x " + str(self.mlthresh[i]) + " < z y ?"
                    mask = core.std.Expr([clip,tmask,mask], expr)
                mask = core.std.Expr(mask, "x " + str(self.multi) + " *", self.outdepth)            
            
            else:
                mask = core.tcanny.TCanny(clip, sigma=self.sigma, t_h=self.t_h, mode=0, planes=0)
        
            if self.mpand is not 0:
                mask = self.mExpand(mask, self.mpand[0])
                mask = self.mInpand(mask, self.mpand[1])
            
            return core.rgvs.RemoveGrain(mask, 20)

    class mCannySobel(mParent):
        def __init__(self, mthr, mthr2, mlthresh, mpand):
            super(mCannySobel, self).__init__()
            self.binarize = self.mParaInit(mthr, 48)
            self.sigma = self.mParaInit(mthr2, 1.2)
            self.mlthresh = mlthresh
            self.mpand = mpand
        
        def mCheckList(self, list1, list2):
            if len(list1) != (len(list2) - 1):
                raise ValueError(FUNCNAME + ': num of mthr and mlthresh mismatch !')
    
        def getMask(self, clip):
            clip = self.mGetGray(clip)
            eemask = core.tcanny.TCanny(clip, sigma=self.sigma, mode=1, op=2, planes=0)
            if isinstance(self.binarize, list):
                self.mCheckList(self.mlthresh, self.binarize)
                expr = "x " + str(self.binarize[0]) + " < 0 255 ?"
                mask = core.std.Expr(eemask, expr, self.outdepth)
            
                for i in range(len(self.mlthresh)):
                    texpr = "x " + str(self.binarize[i+1]) + " < 0 255 ?"
                    tmask = core.std.Expr(eemask, texpr)
                    expr = "x " + str(self.mlthresh[i]) + " < z y ?"
                    mask = core.std.Expr([clip,tmask,mask], expr) 
                mask = core.std.Expr(mask, "x " + str(self.multi) + " *", outdepth)
            
            else:
                expr = "x " + str(self.binarize) + " < 0 255 " + str(self.multi) + " * ?"
                mask = core.std.Expr(eemask, expr, self.outdepth)
            
            if self.mpand is not 0:
                mask = self.mExpand(mask, self.mpand[0])
                mask = self.mInpand(mask, self.mpand[1])

            return core.rgvs.RemoveGrain(mask, 20)
    
    class mText(mParent):
        def __init__(self, luma):
            super(mText, self).__init__()
            self.luma = luma
            self.uvdiff = 1
            #self.neutral = 128
            #self.max = 255
        
        def getMask(self, clip):
            y = core.std.ShufflePlanes(clip, 0, vs.GRAY)
            u = mvf.Depth(core.fmtc.resample(core.std.ShufflePlanes(clip, 1, vs.GRAY), W, H, sx=0.25), PROCE_DEPTH)
            v = mvf.Depth(core.fmtc.resample(core.std.ShufflePlanes(clip, 2, vs.GRAY), W, H, sx=0.25), PROCE_DEPTH)
            txtExpr = "x {luma} > y 128 - abs {uvdiff} <= and z 128 - abs {uvdiff} <= and 255 0 ?".format(luma=self.luma, uvdiff=self.uvdiff)
            txtmask = core.std.Expr([y,u,v], txtExpr, self.outdepth)
            if BPS == 16:
                txtmask = core.std.Expr(txtmask, "x 257 *", vs.GRAY16)
            txtmask = core.std.Maximum(txtmask).std.Maximum().std.Maximum()
            return txtmask
            
################### End of Mtype ######################


################### Begin of Main Workflow ################

    input8 = input if BPS == 8 else mvf.Depth(input, 8)
    if BPS == 16 and down8 == True:
        input = input8
    
    # Pre-Antialiasing
    preaaClip = input if preaa == 0 else Preaa(input, preaa)
    
    # Pre-Lineplay (Considered useless)
    lineplayClip = preaaClip if (thin == 0 and dark == 0) else Lineplay(preaaClip, thin, dark)
    
    # Instantiate Main Anti-Aliasing Object, pn is a dict
    if aatype == 1 or aatype == "Eedi2":
        aaObj = aaEedi2(pn)
        
    elif aatype == 2 or aatype == "Eedi3":
        aaObj = aaEedi3(pn)
        
    elif aatype == 3 or aatype == "Nnedi3":
        aaObj = aaNnedi3(pn)
        
    elif aatype == 5 or aatype == "Spline64NrSangNom":
        aaObj = aaSpline64NrSangNom(pn)
        
    elif aatype == 6 or aatype == "Spline64SangNom":
        aaObj = aaSpline64SangNom(pn)
        
    elif aatype == "PointSangNom":
        aaObj = aaPointSangNom(pn)
        
    elif aatype == -1 or aatype == "Eedi2SangNom":
        aaObj = aaEedi2SangNom(pn)
        
    elif aatype == -2 or aatype == "Eedi3SangNom":
        aaObj = aaEedi3SangNom(pn)
        
    elif aatype == -3 or aatype == -4 or aatype == "Nnedi3SangNom":
        aaObj = aaNnedi3SangNom(pn)
        
    else:
        pass
        
    # Get Anti-Aliasing Clip
    if aatype != 0:
        if strength != 0:
            lineplayClip = aaObj.aaResizer(lineplayClip, aaObj.dw, aaObj.dh, 0)
        aaedClip = aaObj.AA(lineplayClip)
        # Cycle it as you will
        while cycle > 0:
            aaedClip = aaObj.AA(aaedClip)
            cycle = cycle - 1
            
    else:
        aaedClip = lineplayClip
        
    # Back 16 if BPS is 16 and down8
    if BPS == 16 and down8 == True:
        aaedClip = mvf.Depth(aaedClip, 16)
        
    # Sharp it
    sharpedClip = aaedClip if sharp == 0 else Sharp(aaedClip, src, sharp)
    
    # Repair it
    repairedClip = sharpedClip if repair == 0 else core.rgvs.Repair(src, sharpedClip, repair)
    
    # Stabilize it
    stabedClip = repairedClip if stabilize == 0 else Stabilize(repairedClip, src, stabilize)
    
    
    # Build AA Mask First then Merge it. Output depth is BPS
          # ! Mask always being built under 8 bit ! #
    if mclip is not None:
        aaMask = mclip
        try:
            mergedClip = core.std.MaskedMerge(src, stabedClip, aaMask, planes=[0,1,2], first_plane=True)
        except:
            raise RuntimeError(FUNCNAME + ': Something wrong with your mclip. Check the resolution and bitdepth of mclip !')
    else:
        if mtype != 0:
            if mtype == 1 or mtype == "Canny":
                maskObj = mCanny(mthr, mthr2, mlthresh, mpand)
                aaMask = maskObj.getMask(input8)
            elif mtype == 2 or mtype == "CannySobel":
                maskObj = mCannySobel(mthr, mthr2, mlthresh, mpand)
                aaMask = maskObj.getMask(input8)
            else:
                pass
            
            # Let it back to 16 if down8
            if BPS == 16 and down8 == True:
                aaMask = core.std.Expr(aaMask, "x 257 *", vs.GRAY16)
                
            mergedClip = core.std.MaskedMerge(src, stabedClip, aaMask, planes=[0,1,2], first_plane=True)
    
    # Build Text Mask if input is not GRAY
    if IS_GRAY == False and txtprt is not None:
        txtmObj = mText(txtprt)
        txtMask = txtmObj.getMask(input8)
        txtprtClip = core.std.MaskedMerge(mergedClip, src, txtMask, planes[0,1,2], first_plane=True)
    else:
        txtprtClip = mergedClip
    
    
    # Clamp loss if input is 16bit and down8 is set
    if BPS == 16 and down8 == True:
        outClip = mvf.LimitFilter(src, txtprtClip, thr=1.0, elast=2.0)
    else:
        outClip = txtprtClip
        
    # Showmask or output
    if showmask == -1:
        try:
            return txtMask
        except UnboundLocalError:
            raise RuntimeError(FUNCNAME + ': No txtmask to show if you don\'t have one.')
            
    elif showmask == 1:
        try:
            return aaMask
        except UnboundLocalError:
            raise RuntimeError(FUNCNAME + ': No mask to show if you don\'t have one.')
    elif showmask == 2:
        try:
            return core.std.StackVertical([core.std.ShufflePlanes([aaMask,core.std.BlankClip(src)], [0,1,2], vs.YUV),src])
        except UnboundLocalError:
            raise RuntimeError(FUNCNAME + ': No mask to show if you don\'t have one.')
    elif showmask == 3:
        try:
            return core.std.Interleave([core.std.ShufflePlanes([aaMask,core.std.BlankClip(src)], [0,1,2], vs.YUV),src])
        except UnboundLocalError:
            raise RuntimeError(FUNCNAME + ': No mask to show if you don\'t have one.')
    else:
        return outClip








# Old TAAmbk. May be deleted soon. 
def TAAmbk(input, aatype=1, lsb=False, preaa=0, sharp=0, postaa=None, mtype=None, mthr=32, src=None,
			 cycle=0, eedi3sclip=None, predown=False, repair=None, stabilize=0, p1=None, p2=None, 
		   p3=None, p4=None, p5=None, p6=None, showmask=False, mtype2=0, mthr2=32, auxmthr=None):
	core = vs.get_core()
	
	#constant value
	funcname = 'TAAmbk'
	w = input.width
	h = input.height
	upw4 = (round(w*0.09375)*16) # mod16(w*1.5)
	uph4 = (round(h*0.09375)*16) # mod16(h*1.5)
	downw4 = (round(w*0.046875)*16) # mod16(w*0.75)
	downh4 = (round(h*0.046875)*16) # mod16(h*0.75)
	
	if input.format.num_planes == 1:
		GRAY = True
	else:
		GRAY = False
	
	# border to add for SangNomMod when aatype = 6 or 7
	if aatype == 6 or aatype == 7:
		# mod16 or not
		if w % 16 == 0:
			mod16w = True
		else:
			mod16w = False
			borderW = (16 - w % 16) 
		if h % 16 == 0:
			mod16h = True
		else:
			mod16h = False
			borderH = (16 - h % 16)
	
	
	
	#generate paramerters if None
	if mtype == None:
		if preaa == 0 and aatype == 0:
			mtype = 0
		else:
			mtype = 1
	
	if auxmthr == None:
		if mtype == 1:
			auxmthr = 1.2
		else:
			if mtype ==3:
				auxmthr = 8
			else:
				auxmthr = 0.0
							
	absSh = abs(sharp)
	if postaa == None:
		if absSh > 70 or (absSh > 0.4 and absSh < 1):
			postaa = True
		else:
			postaa = False
			
	if repair == None:
		if (aatype != 1 and aatype != 2 and aatype != 3):
			repair = 20
		else:
			repair = 0
	
	if isinstance(mtype, vs.VideoNode):
		rp = 20
	else:
		if mtype == 5:
			rp = 0
		else:
			rp = 20
	
	if eedi3sclip is None:
		eedi3sclip = False
	else:
		if not isinstance(eedi3sclip, bool):
			raise TypeError(funcname + ': \"eedi3sclip\" must be bool !')
			
	
	# p1~p6 preset groups	
	pindex = aatype + 3
	#				 aatype =		-3       -2		-1		0	   1	  2	 	3		 4		 5		 6		7
	if p1	is None: p1		=	[	48,	    48,		48,		0,	   10,	 0.5, 	 3,		48,		48,		48,		48][pindex]
	if p2	is None: p2		=	[	 3,	   0.5,		10,		0,	   20,	 0.2, 	 1,		 1,		 0,		rp,		rp][pindex]
	if p3	is None: p3		=	[	 1,	   0.2,		20,		0,	   20,	  20, 	 2,		 3,		 0,		 0,		 0][pindex]
	if p4	is None: p4		=	[	 2,	    20,		20,		0,	   24,	   3, 	 0,		 2,		 0,		 0,		 0][pindex]
	if p4	is None: p4		=	[	 2,	    20,		20,		0,	   24,	   3, 	 0,		 2,		 0,		 0,		 0][pindex]
	if p5	is None: p5		=	[	 0,	     3,		24,		0,	   50,	  30, 	 0,		 0,		 0,		 0,		 0][pindex]
	if p6	is None: p6		=	[	 0,	    30,		50,		0,	    0,	   0, 	 0,		 0,		 0,		 0,		 0][pindex]
	
	
	#paramerters check
	#input type check
	if not isinstance(input, vs.VideoNode):
		raise ValueError(funcname + ': \"input\" must be a clip !')
	#YUV constant value
	inputFormatid = input.format.id  							# A unique id identifying the format.
	sColorFamily = input.format.color_family					# Which group of colorspaces the format describes.
	sbits_per_sample = int(input.format.bits_per_sample)		# How many bits are used to store one sample in one plane.
	sSType = input.format.sample_type							# source sample type
	#format check
	if sColorFamily == vs.YUV or sColorFamily == vs.GRAY:
		if sSType != vs.INTEGER:
			raise TypeError(funcname + ': \"input\" must be INTEGER format !')
		else:
			if not (sbits_per_sample == 8 or sbits_per_sample == 16):
				raise TypeError(funcname + ': \"input\" must be 8bit or 16bit INTEGER !')
	else:
		raise TypeError(funcname + ': Only YUV colorfmaily is supported !')
	
	#aatype check
	if not isinstance(aatype, int) or (aatype < -3 or aatype > 7):
		raise ValueError(funcname + ': \"aatype\" (int: -3~7) invalid !')
	#lsb check
	if not isinstance(lsb, bool):
		raise TypeError(funcname + ': \"lsb\" must be BOOL !')
	#preaa check
	if not isinstance(preaa, int) or (preaa < 0 or preaa > 1):
		raise ValueError(funcname + ': \"preaa\" (int: 0~1) invalid !')
	#mtype check
	if not isinstance(mtype, int):
		if not isinstance(mtype, vs.VideoNode):
			raise TypeError(funcname + ': \"mtype\" is not a clip !')
		else:
			if mtype.format.id != inputFormatid :
				raise TypeError(funcname + ': \"input\" and \"mclip(mtype)\" must be of the same format !')
			else:
				if mtype.width != w or mtype.height != h:
					raise TypeError(funcname + ': resolution of \"input\" and your custome mask clip \"mtype\" must match !')
	else:
		if mtype < 0 or mtype > 6:
			raise ValueError(funcname + ': \"mtype\" (int: 0~6) invalid !')
	#mthr check
	if not isinstance(mthr, int) or (mthr < 0 or mthr > 255):
		raise ValueError(funcname + ': \"mthr\" (int: 0~255) invalid !')
	#repair check
	if not isinstance(repair, int) or (repair < -24 or repair > 24):
		raise ValueError(funcname + ': \"repair\" (int: -24~24) invalid !')
	#src clip check
	if src is not None and isinstance(src, vs.VideoNode):
		if src.format.id != inputFormatid :
			raise TypeError(funcname + ': \"input\" and \"src\" must be of the same format !')
		else:
			if src.width != w or src.height != h:
				raise TypeError(funcname + ': resolution of \"input\" and \"src\" must match !')
	elif src is not None:
		raise ValueError(funcname + ': \"src\" is not a clip !')
	#cycle check
	if not isinstance(cycle, int) or cycle < 0:
		raise ValueError(funcname + ': \"cycle\" must be non-negative int !')
	#stabilize check
	if not isinstance(stabilize, int) or (stabilize < -3 or stabilize > 3):
		raise ValueError(funcname + ': \"stabilize\" (int: -3~3) invalid !')
	if showmask and mtype == 0:
		raise ValueError(funcname + ': There is NO mask to show when \"mtype\" = 0 !')
		
	###################################
	###  Small functions ##############
	###################################
	
	# average two clips of 3 yuv planes
	def average(clipa, clipb):
		return (core.std.Expr(clips=[clipa,clipb], expr=["x y + 2 /"]))
		
	# bitdepth conversion from mvsfunc, mawen1250 Thanks!
	def Depth(input, depth=None):
		sbitPS = input.format.bits_per_sample
		if sbitPS == depth:
			return input
		else:
			return core.fmtc.bitdepth(input,bits=depth,flt=0,dmode=3)
			
	# fast PointResize from mvsfunc
	def PointPower(input, vpow=1):
		for i in range(vpow):
			clip = core.std.Interleave([input,input]).std.DoubleWeave(tff=True).std.SelectEvery(2,0)
		return clip
		
	
	###################################
	
	# src clip issue
	#======================
	if src == None:
		if predown:
			if lsb:
				src = core.nnedi3.nnedi3(core.fmtc.resample(input, w=downw4, h=downh4,kernel="spline36"),field=1,dh=True)
				src = core.std.Transpose(core.fmtc.resample(src,w=downw4,h=h,sx=0,sy=[-0.5,-0.5*(1<<input.format.subsampling_h)],kernel="spline36"))
				src = core.std.Transpose(core.fmtc.resample(core.nnedi3.nnedi3(src,field=1,dh=True),w=h,h=w,sx=0,sy=[-0.5,-0.5*(1<<input.format.subsampling_h)],kernel="spline36"))
			else:
				src = core.nnedi3.nnedi3(Depth(core.fmtc.resample(input, w=downw4, h=downh4,kernel="spline36"),8),field=1,dh=True)
				src = core.std.Transpose(core.fmtc.resample(src,w=downw4,h=h,sx=0,sy=[-0.5,-0.5*(1<<input.format.subsampling_h)],kernel="spline36"))
				src = core.std.Transpose(core.fmtc.resample(core.nnedi3.nnedi3(Depth(src,8),field=1,dh=True),w=h,h=w,sx=0,sy=[-0.5,-0.5*(1<<input.format.subsampling_h)],kernel="spline36"))
		else:
			src = input
	#======================
	

	
	#internal function
	def TAAmbk_prepass(clip, predown=predown, downw4=downw4, downh4=downh4, thin=0, dark=0, preaa=preaa):
		if predown:
			pdclip = core.resize.Spline36(clip, downw4, downh4)
		else:
			pdclip = clip
		
		if preaa == 1:
			if lsb:
				nn = core.nnedi3.nnedi3(pdclip, field=3)
				nnt = core.std.Transpose(core.nnedi3.nnedi3(core.std.Transpose(pdclip), field=3))
			else:
				nn = core.nnedi3.nnedi3(Depth(pdclip,8), field=3)
				nnt = core.std.Transpose(core.nnedi3.nnedi3(Depth(core.std.Transpose(pdclip),8), field=3))
			#nnedi3 double rate start with top
			clph = average(core.std.SelectEvery(nn, cycle=2, offsets=0), core.std.SelectEvery(nn, cycle=2, offsets=1))
			clpv = average(core.std.SelectEvery(nnt, cycle=2, offsets=0), core.std.SelectEvery(nnt, cycle=2, offsets=1))
			clp = average(clph, clpv)
			
			preaaB = clp
		else:
			preaaB = pdclip
		preaaC = preaaB
		#filters unavailable
		#=======================================
		# if thin == 0 and dark == 0:
			# preaaC = preaaB
		
		# else:
			# if dark == 0:
				# preaaC = core.warp.AWarpSharp2(preaaB,depth=thin)
			# elif thin == 0:
				# preaaC = Toon(preaaB,dark) #?
			# else:
				# preaaC = Toon(core.warp.AWarpSharp2(preaaB,depth=thin),dark)  #?
		#=======================================
		
		
		return preaaC
		
		
		
		
		
	#internal functions
	def TAAmbk_mainpass(preaaC, aatype=aatype, cycle=cycle, p1=p1, p2=p2, p3=p3, p4=p4, p5=p5, p6=p6, w=w, h=h,
						uph4=uph4, upw4=upw4, eedi3sclip=eedi3sclip):
		# generate eedi3 sclip using nnedi3 double height				
		if eedi3sclip is True:
			if aatype == -2:
				if lsb:
					sclip = core.nnedi3.nnedi3(preaaC,field=1,dh=True)
					sclip_r = core.resize.Spline36(sclip,w,uph4)
					sclip_r = core.std.Transpose(sclip_r)
					sclip_r = core.nnedi3.nnedi3(sclip_r,field=1,dh=True)
					sclip = Depth(sclip,8)
					sclip_r = Depth(sclip_r,8)
				else:
					sclip = core.nnedi3.nnedi3(Depth(preaaC,8),field=1,dh=True)
					sclip_r = core.resize.Spline36(sclip,w,uph4)
					sclip_r = core.std.Transpose(sclip_r)
					sclip_r = core.nnedi3.nnedi3(sclip_r,field=1,dh=True)
			elif aatype == 2:
				if lsb:
					sclip = core.nnedi3.nnedi3(preaaC,field=1,dh=True)
					sclip_r = sclip_r = core.resize.Spline36(sclip,w,h)
					sclip_r = core.std.Transpose(sclip_r)
					sclip_r = core.nnedi3.nnedi3(sclip_r,field=1,dh=True)
					sclip = Depth(sclip,8)
					sclip_r = Depth(sclip_r,8)
				else:
					sclip = core.nnedi3.nnedi3(Depth(preaaC,8),field=1,dh=True)
					sclip_r = sclip_r = core.resize.Spline36(sclip,w,h)
					sclip_r = core.std.Transpose(sclip_r)
					sclip_r = core.nnedi3.nnedi3(sclip_r,field=1,dh=True)
		
		# generate aa_clip
		##########################
		# # # AAtype -3 or 4 # # #
		##########################
		if aatype == -3 or aatype == 4:
			if lsb:
				aa_clip = core.nnedi3.nnedi3(preaaC, dh=True, field=1, nsize=int(p2), nns=int(p3), qual=int(p4))
				aa_clip = core.std.Transpose(core.fmtc.resample(aa_clip,w=w,h=uph4,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36"))
				aa_clip = core.fmtc.resample(core.nnedi3.nnedi3(aa_clip, dh=True, field=1, nsize=int(p2), nns=int(p3), qual=int(p4)),w=uph4,h=upw4,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
				aa_clip = Depth(aa_clip,depth=8)
				aa_clip = core.sangnom.SangNomMod(core.std.Transpose(core.sangnom.SangNomMod(aa_clip,aa=int(p1))),aa=int(p1))
				aa_clip = core.fmtc.resample(aa_clip,w=w,h=h,kernel=["spline36","spline36"])
			else:
				aa_clip = core.nnedi3.nnedi3(Depth(preaaC,8), dh=True, field=1, nsize=int(p2), nns=int(p3), qual=int(p4))
				aa_clip = core.std.Transpose(core.fmtc.resample(aa_clip,w=w,h=uph4,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36"))
				aa_clip = core.fmtc.resample(core.nnedi3.nnedi3(Depth(aa_clip,8), dh=True, field=1, nsize=int(p2), nns=int(p3), qual=int(p4)),w=uph4,h=upw4,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
				aa_clip = Depth(aa_clip,depth=8)
				aa_clip = core.sangnom.SangNomMod(core.std.Transpose(core.sangnom.SangNomMod(aa_clip,aa=int(p1))),aa=int(p1))
				aa_clip = core.fmtc.resample(aa_clip,w=w,h=h,kernel=["spline36","spline36"])
		######################
		# # # AA type -2 # # #
		######################
		elif aatype == -2:
			if eedi3sclip == False:
					
				aa_clip = core.fmtc.resample(core.eedi3.eedi3(Depth(preaaC,8), dh=True, field=1, alpha=p2, beta=p3, gamma=p4, nrad=int(p5), mdis=int(p6)), w=w, h=uph4, sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
				aa_clip = Depth(aa_clip,depth=8)
				aa_clip = core.eedi3.eedi3(core.std.Transpose(aa_clip), dh=True, field=1, alpha=p2, beta=p3, gamma=p4, nrad=int(p5), mdis=int(p6))
				aa_clip = core.sangnom.SangNomMod(Depth(core.fmtc.resample(aa_clip, w=uph4, h=upw4, sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36"),depth=8),aa=int(p1))
				aa_clip = core.sangnom.SangNomMod(core.std.Transpose(aa_clip),aa=int(p1))
				aa_clip = core.fmtc.resample(aa_clip,w=w,h=h,kernel=["spline36","spline36"])
			else:
				# EEDI3 need w * h
				aa_clip = core.fmtc.resample(core.eedi3.eedi3(Depth(preaaC,8), dh=True, field=1, alpha=p2, beta=p3, gamma=p4, nrad=int(p5), mdis=int(p6), sclip=sclip), w=w, h=uph4, sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
				# output w * uph4
				aa_clip = Depth(aa_clip,depth=8)
				# EEDI3 need uph4 * w
				aa_clip = core.eedi3.eedi3(core.std.Transpose(aa_clip), dh=True, field=1, alpha=p2, beta=p3, gamma=p4, nrad=int(p5), mdis=int(p6), sclip=sclip_r)
				aa_clip = core.sangnom.SangNomMod(Depth(core.fmtc.resample(aa_clip, w=uph4, h=upw4, sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36"),depth=8),aa=int(p1))
				aa_clip = core.sangnom.SangNomMod(core.std.Transpose(aa_clip),aa=int(p1))
				aa_clip = core.fmtc.resample(aa_clip,w=w,h=h,kernel=["spline36","spline36"])
		######################
		# # # AA type -1 # # #
		######################
		elif aatype == -1:
			aa_clip = core.fmtc.resample(core.eedi2.EEDI2(preaaC, field=1, mthresh=int(p2), lthresh=int(p3), vthresh=int(p4), maxd=int(p5), nt=int(p6)),w=w,h=uph4,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
			aa_clip = core.eedi2.EEDI2(core.std.Transpose(aa_clip),field=1, mthresh=int(p2), lthresh=int(p3), vthresh=int(p4), maxd=int(p5), nt=int(p6))
			aa_clip = core.sangnom.SangNomMod(Depth(core.fmtc.resample(aa_clip,w=uph4,h=upw4,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36"),depth=8),aa=int(p1))
			aa_clip = core.sangnom.SangNomMod(core.std.Transpose(aa_clip),aa=int(p1))
			aa_clip = core.fmtc.resample(aa_clip,w=w,h=h,kernel=["spline36","spline36"])
		######################
		# # # AA type 1  # # #
		######################
		elif aatype == 1:
			aa_clip = core.fmtc.resample(core.eedi2.EEDI2(preaaC,field=1,mthresh=int(p1), lthresh=int(p2), vthresh=int(p3), maxd=int(p4), nt=int(p5)),w=w,h=h,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
			aa_clip = core.eedi2.EEDI2(core.std.Transpose(aa_clip),field=1,mthresh=int(p1), lthresh=int(p2), vthresh=int(p3), maxd=int(p4), nt=int(p5))
			aa_clip = core.std.Transpose(core.fmtc.resample(aa_clip,w=h,h=w,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36"))
		######################
		# # # AA type 2  # # #
		######################
		elif aatype == 2:
			if eedi3sclip == False:
				aa_clip = core.fmtc.resample(core.eedi3.eedi3(Depth(preaaC,8),dh=True, field=1, alpha=p1, beta=p2, gamma=p3, nrad=int(p4), mdis=int(p5)),w=w,h=h,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
				aa_clip = Depth(core.std.Transpose(aa_clip),depth=8)
				aa_clip = core.fmtc.resample(core.eedi3.eedi3(aa_clip,dh=True, field=1, alpha=p1, beta=p2, gamma=p3, nrad=int(p4), mdis=int(p5)),w=h,h=w,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
				aa_clip = core.std.Transpose(aa_clip)
			else:
				#EEDI3 need w * h
				aa_clip = core.fmtc.resample(core.eedi3.eedi3(Depth(preaaC,8),dh=True, field=1, alpha=p1, beta=p2, gamma=p3, nrad=int(p4), mdis=int(p5), sclip=sclip),w=w,h=h,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
				#output w * h
				aa_clip = Depth(core.std.Transpose(aa_clip),depth=8)
				#EEDI3 need h * w
				aa_clip = core.fmtc.resample(core.eedi3.eedi3(aa_clip,dh=True, field=1, alpha=p1, beta=p2, gamma=p3, nrad=int(p4), mdis=int(p5), sclip=sclip_r),w=h,h=w,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
				aa_clip = core.std.Transpose(aa_clip)
		######################
		# # # AA type 3  # # #
		######################
		elif aatype == 3:
			if lsb:
				aa_clip = core.fmtc.resample(core.nnedi3.nnedi3(preaaC, dh=True, field=1, nsize=int(p1), nns=int(p2), qual=int(p3)),w=w,h=h,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
				aa_clip = core.nnedi3.nnedi3(core.std.Transpose(aa_clip), dh=True, field=1, nsize=int(p1), nns=int(p2), qual=int(p3))
				aa_clip = core.std.Transpose(core.fmtc.resample(aa_clip,w=h,h=w,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36"))
			else:
				aa_clip = core.fmtc.resample(core.nnedi3.nnedi3(Depth(preaaC,8), dh=True, field=1, nsize=int(p1), nns=int(p2), qual=int(p3)),w=w,h=h,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
				aa_clip = core.nnedi3.nnedi3(Depth(core.std.Transpose(aa_clip),8), dh=True, field=1, nsize=int(p1), nns=int(p2), qual=int(p3))
				aa_clip = core.std.Transpose(core.fmtc.resample(aa_clip,w=h,h=w,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36"))
		######################
		# # # AA type 5  # # #
		######################
		elif aatype == 5:
			aa_clip = Depth(core.fmtc.resample(preaaC, w=upw4, h=uph4 ,kernel=["lanczos","bicubic"]),depth=8)
			aa_clip = core.std.Transpose(core.sangnom.SangNomMod(aa_clip,aa=int(p1)))
			aa_clip = core.fmtc.resample(core.sangnom.SangNomMod(aa_clip,aa=int(p1)),w=h,h=w,kernel="spline36")
			aa_clip = core.std.Transpose(aa_clip)
		######################
		# # # AA type 6  # # #
		######################
		elif aatype == 6:
			aa_clip = Depth(core.fmtc.resample(preaaC, w=w, h=uph4 ,kernel=["lanczos","bicubic"]),depth=8)
			if mod16w is True:
				aa_clip = core.fmtc.resample(core.sangnom.SangNomMod(aa_clip,aa=int(p1)),w=w,h=h,kernel="spline36")
			else:
				aa_clip = core.std.AddBorders(aa_clip,borderW)
				aa_clip = core.fmtc.resample(core.sangnom.SangNomMod(aa_clip,aa=int(p1)),w=w,h=h,kernel="spline36")
				aa_clip = core.std.CropRel(aa_clip,borderW)
			aa_clip = core.fmtc.resample(core.std.Transpose(aa_clip),w=h,h=upw4,kernel=["lanczos","bicubic"])
			if mod16h is True:
				aa_clip = core.sangnom.SangNomMod(Depth(aa_clip,depth=8),aa=int(p1))
			else:
				aa_clip = core.std.AddBorders(aa_clip,borderH)
				aa_clip = core.sangnom.SangNomMod(Depth(aa_clip,depth=8),aa=int(p1))
				aa_clip = core.std.CropRel(aa_clip,borderH)
			aa_clip = core.std.Transpose(core.fmtc.resample(aa_clip,w=h,h=w,kernel="spline36"))
			aa_clip = core.rgvs.Repair(aa_clip, core.fmtc.resample(preaaC,w=w,h=h,kernel="spline64"), mode=int(p2))
		######################
		# # # AA type 7  # # #
		######################
		elif aatype == 7:
			aa_clip = PointPower(Depth(preaaC,8))
			
			if mod16w and not predown:
				aa_clip = core.sangnom.SangNomMod(aa_clip,aa=int(p1))
				aa_clip = core.std.Transpose(aa_clip)
			elif predown:
				if aa_clip.width == downw4:
					aa_clip = core.sangnom.SangNomMod(aa_clip,aa=int(p1))
					aa_clip = core.std.Transpose(aa_clip)
				elif mod16w:
					aa_clip = core.sangnom.SangNomMod(aa_clip,aa=int(p1))
					aa_clip = core.std.Transpose(aa_clip)
				else:
					aa_clip = core.std.AddBorders(aa_clip,borderW)
					aa_clip = core.sangnom.SangNomMod(aa_clip,aa=int(p1))
					aa_clip = core.std.CropRel(aa_clip,borderW)
					aa_clip = core.std.Transpose(aa_clip)
			else:
				aa_clip = core.std.AddBorders(aa_clip,borderW)
				aa_clip = core.sangnom.SangNomMod(aa_clip,aa=int(p1))
				aa_clip = core.std.CropRel(aa_clip,borderW)
				aa_clip = core.std.Transpose(aa_clip)
			aa_clip = PointPower(aa_clip)
			
			if mod16h and not predown:
				aa_clip = core.sangnom.SangNomMod(aa_clip,aa=int(p1))
			elif predown:
				if aa_clip.width == downh4 * 2:
					aa_clip = core.sangnom.SangNomMod(aa_clip,aa=int(p1))
				elif mod16h:
					aa_clip = core.sangnom.SangNomMod(aa_clip,aa=int(p1))
				else:
					aa_clip = core.std.AddBorders(aa_clip,(16 - h * 2 % 16))
					aa_clip = core.sangnom.SangNomMod(aa_clip,aa=int(p1))
					aa_clip = core.std.CropRel(aa_clip,(16 - h * 2 % 16))
			else:
				aa_clip = core.std.AddBorders(aa_clip,(16 - h * 2 % 16))
				aa_clip = core.sangnom.SangNomMod(aa_clip,aa=int(p1))
				aa_clip = core.std.CropRel(aa_clip,(16 - h * 2 % 16))
			aa_clip = core.std.Transpose(core.fmtc.resample(aa_clip,w=h,h=w,kernel="spline36"))
			
			if predown:
				aa_clip = core.rgvs.Repair(aa_clip, core.fmtc.resample(preaaC,w=w,h=h,kernel="spline64"), mode=int(p2))
			else:
				aa_clip = core.rgvs.Repair(aa_clip, Depth(preaaC,16), mode=int(p2))
			
		# if predown and no aa, use nnedi3 to recover
		else:
			if predown:
				if lsb:
					aa_clip = core.fmtc.resample(core.nnedi3.nnedi3(preaaC,dh=True, field=1, nsize=1, nns=3, qual=2),w=preaaC.width,h=h,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
					aa_clip = core.nnedi3.nnedi3(core.std.Transpose(aa_clip),dh=True, field=1, nsize=1, nns=3, qual=2)
					aa_clip = core.std.Transpose(core.fmtc.resample(aa_clip,w=h,h=w,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36"))
				else:
					aa_clip = core.fmtc.resample(core.nnedi3.nnedi3(Depth(preaaC,8),dh=True, field=1, nsize=1, nns=3, qual=2),w=preaaC.width,h=h,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
					aa_clip = core.nnedi3.nnedi3(Depth(core.std.Transpose(aa_clip),8),dh=True, field=1, nsize=1, nns=3, qual=2)
					aa_clip = core.std.Transpose(core.fmtc.resample(aa_clip,w=h,h=w,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36"))
		
		return aa_clip if cycle == 0 else TAAmbk_mainpass(aa_clip, aatype=aatype ,cycle=cycle-1, p1=p1, p2=p2, p3=p3, p4=p4, p5=p5, p6=p6, w=w, h=h, uph4=uph4, upw4=upw4, eedi3sclip=eedi3sclip)
	
	
	
	
	#Internal functions
	def TAAmbk_mask(input, mtype=mtype, mthr=mthr, w=w, mtype2=mtype2, mthr2=mthr2, auxmthr=auxmthr):
		bits = input.format.bits_per_sample
		shift = bits - 8
		neutral = 128 << shift
		peak = (1 << bits) - 1
		multiple = peak / 255
		#generate edge_mask_1
		if mtype == 1:
			edge_mask_1 = core.tcanny.TCanny(input, sigma=auxmthr, mode=1, op=2, planes=0)
			exprY = "x "+str(mthr*multiple)+" <= x 2 / x 2 * ?"
			edge_mask_1 = core.std.Expr(edge_mask_1, [exprY] if GRAY else [exprY,""])
			if w > 1100:
				edge_mask_1 = core.rgvs.RemoveGrain(edge_mask_1, [20] if GRAY else [20,0])
			else:
				edge_mask_1 = core.rgvs.RemoveGrain(edge_mask_1, [11] if GRAY else [11,0])
			edge_mask_1 = core.generic.Inflate(edge_mask_1, planes=0)
		elif mtype == 3:
			edge_mask_1 = core.generic.TEdge(input, min=auxmthr, planes=0)
			exprY = "x "+str(mthr*multiple/5)+" <= x 2 / x 16 * ?"
			edge_mask_1 = core.std.Expr(edge_mask_1, [exprY] if GRAY else [exprY,""])
			edge_mask_1 = core.generic.Deflate(edge_mask_1, planes=0)
			if w > 1100:
				edge_mask_1 = core.rgvs.RemoveGrain(edge_mask_1, [20] if GRAY else [20,0])
			else:
				edge_mask_1 = core.rgvs.RemoveGrain(edge_mask_1, [11] if GRAY else [11,0])
		elif mtype == 2:
			edge_mask_1 = core.msmoosh.MSharpen(input, threshold=mthr//5, strength=0, mask=True, planes=0)
		elif mtype == 4:
			edge_mask_1 = core.generic.Sobel(input, min=5, max=7, planes=0)
			edge_mask_1 = core.generic.Inflate(edge_mask_1, planes=0)
		elif mtype == 5:
			edge_mask_1 = core.std.Convolution(input,[0, 0, 0, 0, 2, -1, 0, -1, 0],planes=0)
			edge_mask_1 = core.generic.Inflate(edge_mask_1, planes=0)
		elif mtype == 6:
			edgemask1 = core.std.Convolution(input,[1, 1, 0, 1, 0, -1, 0, -1, -1],divisor=1,saturate=False,planes=0)
			edgemask2 = core.std.Convolution(input,[1, 1, 1, 0, 0, 0, -1, -1, -1],divisor=1,saturate=False,planes=0)
			edgemask3 = core.std.Convolution(input,[1, 0, -1, 1, 0, -1, 1, 0, -1],divisor=1,saturate=False,planes=0)
			edgemask4 = core.std.Convolution(input,[0, -1, -1, 1, 0, -1, 1, 1, 0],divisor=1,saturate=False,planes=0)
			mt = "x y max z max a max"
			edge_mask_1 = core.std.Expr([edgemask1,edgemask2,edgemask3,edgemask4],[mt] if GRAY else [mt,""])
			exprY = "x "+str(mthr*multiple)+" <= x 2 / x 2.639015821545 * ?"
			edge_mask_1 = core.std.Expr(edge_mask_1, [exprY] if GRAY else [exprY,""])
			edge_mask_1 = core.rgvs.RemoveGrain(edge_mask_1, [4] if GRAY else [4,0])
			edge_mask_1 = core.generic.Inflate(edge_mask_1, planes=0)
		else:
			edge_mask_1 == None
			
		#generate edge_mask_2
		if mtype2 == 0:
			edge_mask_2 = None
		elif mtype2 == 1:
			edge_mask_2 = core.tcanny.TCanny(input, sigma=1.2, mode=1, op=0, planes=0)
			exprY = "x "+str(mthr2*multiple)+" <= x 2 / x 2 * ?"
			edge_mask_2 = core.std.Expr(edge_mask_2, [exprY] if GRAY else [exprY,""])
			if w > 1100:
				edge_mask_2 = core.rgvs.RemoveGrain(edge_mask_2, [20] if GRAY else [20,0])
			else:
				edge_mask_2 = core.rgvs.RemoveGrain(edge_mask_2, [11] if GRAY else [11,0])
			edge_mask_1 = core.generic.Inflate(edge_mask_2, planes=0)
		elif mtype2 == 3:
			edge_mask_2 = core.generic.TEdge(input, planes=0)
			exprY = "x "+str(mthr2*multiple/5)+" <= x 2 / x 16 * ?"
			edge_mask_2 = core.std.Expr(edge_mask_2, [exprY] if GRAY else [exprY,""])
			edge_mask_2 = core.generic.Deflate(edge_mask_2, planes=0)
			if w > 1100:
				edge_mask_2 = core.rgvs.RemoveGrain(edge_mask_2, [20] if GRAY else [20,0])
			else:
				edge_mask_2 = core.rgvs.RemoveGrain(edge_mask_2, [11] if GRAY else [11,0])
		elif mtype2 == 2:
			edge_mask_2 = core.msmoosh.MSharpen(input, threshold=mthr2//5, strength=0, mask=True, planes=0)
		elif mtype2 == 4:
			edge_mask_2 = core.generic.Sobel(input, min=5, max=7, planes=0)
			edge_mask_2 = core.generic.Inflate(edge_mask_2, planes=0)
		elif mtype2 == 5:
			edge_mask_1 = core.std.Convolution(input,[0, 0, 0, 0, 2, -1, 0, -1, 0],planes=0)
			edge_mask_2 = core.generic.Inflate(edge_mask_2, planes=0)
		else:
			edgemask1 = core.std.Convolution(input,[1, 1, 0, 1, 0, -1, 0, -1, -1],divisor=1,saturate=False,planes=0)
			edgemask2 = core.std.Convolution(input,[1, 1, 1, 0, 0, 0, -1, -1, -1],divisor=1,saturate=False,planes=0)
			edgemask3 = core.std.Convolution(input,[1, 0, -1, 1, 0, -1, 1, 0, -1],divisor=1,saturate=False,planes=0)
			edgemask4 = core.std.Convolution(input,[0, -1, -1, 1, 0, -1, 1, 1, 0],divisor=1,saturate=False,planes=0)
			mt = "x y max z max a max"
			edge_mask_2 = core.std.Expr([edgemask1,edgemask2,edgemask3,edgemask4],[mt] if GRAY else [mt,""])
			exprY = "x "+str(mthr2*multiple)+" <= x 2 / x 2.639015821545 * ?"
			edge_mask_2 = core.std.Expr(edge_mask_2, [exprY] if GRAY else [exprY,""])
			edge_mask_2 = core.rgvs.RemoveGrain(edge_mask_2, [4] if GRAY else [4,0])
			edge_mask_2 = core.generic.Inflate(edge_mask_2, planes=0)
			
		#generate final_mask
		if mtype2 == 0:
			final_mask = edge_mask_1
		else:
			final_mask = core.std.Expr([edge_mask_1,edge_mask_2], ["x y max"] if GRAY else ["x y max",""])
			
		return final_mask
	
	
	#temporal stabilizer of sharped clip
	def Soothe(sharp, origin, keep=24):
		bits = sharp.format.bits_per_sample
		shift = bits - 8
		neutral = 128 << shift
		peak = (1 << bits) - 1
		multiple = peak / 255
		const = 100 * multiple
		if keep > 100:
			keep = 100
		if keep < 0:
			keep = 0
		KP = keep*multiple
		mt1 = 'x y - {neutral} +'.format(neutral=neutral)
		diff = core.std.Expr(clips=[origin,sharp], expr=[mt1])
		diff2 = core.focus.TemporalSoften(diff, radius=1, luma_threshold=255, chroma_threshold=255, scenechange=32, mode=2)
		expr = 'x {neutral} - y {neutral} - * 0 < x {neutral} - {const} / {KP} * {neutral} + x {neutral} - abs y {neutral} - abs > x {KP} * y {const} {KP} - * + {const} / x ? ?'.format(neutral=neutral, const=const, KP=KP)
		diff3 = core.std.Expr(clips=[diff,diff2], expr=[expr])
		mt2 = 'x y {neutral} - -'.format(neutral=neutral)
		return core.std.Expr(clips=[origin,diff3], expr=[mt2])
		
	#internal functions
	def TAAmbk_stabilize(input, aaedsharp, stabilize):
		aadiff = core.std.MakeDiff(Depth(input,16), aaedsharp)
		if(stabilize < 0):
			aadiff_stab = core.rgvs.Repair(core.focus.TemporalSoften(aadiff,abs(stabilize), 255, 255, 254, 2),aadiff,4)
		else:
			inputsuper = core.mv.Super(input,pel=1)
			diffsuper = core.mv.Super(aadiff,pel=1,levels=1)
			if stabilize == 3:
				fv3 = core.mv.Analyse(inputsuper,isb=False,delta=3,overlap=8,blksize=16)
				bv3 = core.mv.Analyse(inputsuper,isb=True,delta=3,overlap=8,blksize=16)
			if stabilize >= 2:
				fv2 = core.mv.Analyse(inputsuper,isb=False,delta=2,overlap=8,blksize=16)
				bv2 = core.mv.Analyse(inputsuper,isb=True,delta=2,overlap=8,blksize=16)
			if stabilize >= 1:
				fv1 = core.mv.Analyse(inputsuper,isb=False,delta=1,overlap=8,blksize=16)
				bv1 = core.mv.Analyse(inputsuper,isb=True,delta=1,overlap=8,blksize=16)
				
			if stabilize == 1:
				stabilized_diff = core.mv.Degrain1(aadiff,diffsuper,bv1,fv1)
			elif stabilize == 2:
				stabilized_diff = core.mv.Degrain2(aadiff,diffsuper,bv1,fv1,bv2,fv2)
			elif stabilize == 3:
				stabilized_diff = core.mv.Degrain3(aadiff,diffsuper,bv1,fv1,bv2,fv2,bv3,fv3)
			else:
				stabilized_diff = None
			bits = aadiff.format.bits_per_sample
			shift = bits - 8
			neutral = 128 << shift
			peak = (1 << bits) - 1
			multiple = peak / 255
			mt = 'x {neutral} - abs y {neutral} - abs < x y ?'.format(neutral=neutral)
			aadiff_stab = core.std.Expr(clips=[aadiff,stabilized_diff], expr=[mt])
			aadiff_stab = core.std.Merge(aadiff_stab, stabilized_diff, [0.6] if GRAY else [0.6,0])
		aaed_stab = core.std.MakeDiff(Depth(input,16), aadiff_stab)
		
		return aaed_stab
	#==============================		
	#main functions
	#==============================
	preaaC = TAAmbk_prepass(input, predown=predown, downw4=downw4, downh4=downh4, preaa=preaa)
	
	aa_clip = TAAmbk_mainpass(preaaC,aatype=aatype, cycle=cycle, p1=p1, p2=p2, p3=p3, p4=p4, p5=p5, p6=p6, w=w, h=h, uph4=uph4, upw4=upw4, eedi3sclip=eedi3sclip)
	
	#sharp
	if sharp == 0:
		aaedsp = aa_clip
	elif sharp >= 1:
		aaedsp = haf.LSFmod(aa_clip,strength=int(absSh), defaults="old", source=Depth(src,16))
	elif sharp > 0:
		per = int(40*absSh)
		matrix = [-1, -2, -1, -2, 52-per , -2, -1, -2, -1]
		aaedsp = core.generic.Convolution(aa_clip,matrix)
	elif sharp > -1:
		aaedsp = haf.LSFmod(aa_clip,strength=round(absSh*100), defaults="fast", source=Depth(src,16))
	elif sharp == -1:
		if w > 1100:
			clipb = core.std.MakeDiff(aa_clip, core.rgvs.RemoveGrain(aa_clip, mode=20))
		else:
			clipb = core.std.MakeDiff(aa_clip, core.rgvs.RemoveGrain(aa_clip, mode=11))
		clipb = core.rgvs.Repair(clipb, core.std.MakeDiff(Depth(src,16), aa_clip),mode=13)
		aaedsp = core.std.MergeDiff(aa_clip, clipb)
	else:
		aaedsp = haf.LSFmod(aa_clip,strength=int(absSh), defaults="slow", source=Depth(src,16))
	#postAA
	if postaa:
		aaedsp = Soothe(aaedsp,aa_clip,keep=48)
		
	#stabilize
	if stabilize != 0:
		aaedstab = TAAmbk_stabilize(input, aaedsp, stabilize)
	else:
		aaedstab = aaedsp
	#masked merge
	if isinstance(mtype, vs.VideoNode):
		edge_mask = mtype
		aamerge = core.std.MaskedMerge(Depth(input,16),aaedstab,Depth(edge_mask,16),first_plane=True)
	elif mtype != 0:
		edge_mask = TAAmbk_mask(input, mtype=mtype, mthr=mthr, w=w, mtype2=mtype2, mthr2=mthr2, auxmthr=auxmthr)
		aamerge = core.std.MaskedMerge(Depth(input,16),aaedstab,Depth(edge_mask,16),first_plane=True)
	else:
		aamerge = aaedstab
	# output
	if showmask:
		return edge_mask
	else:
		if repair == 0 or aatype == 0:
			return aamerge
		elif(repair > 0):
			return core.rgvs.Repair(aamerge, Depth(input,depth=16), mode=repair)
		else:
			return core.rgvs.Repair(Depth(input,depth=16), aamerge, mode=abs(repair))




