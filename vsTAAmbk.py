# vsTAAmbk 0.2
# Port from TAAmbk 0.6.1
# Thanks (author)kewenyu for help.

import vapoursynth as vs
import havsfunc as haf
import mvsfunc as mvf


def TAAmbk(input, ignore=False, aatype=1, preaa=1, sharp=None, postaa=None, mtype=None, mthr=32, src=None, cycle=0,
			limit=False, averagemask=False, eedi3sclip=None, predown=False, aarepair=None, stablize=0, p1=None, p2=None, 
		   p3=None, p4=None, p5=None, p6=None, showmask=False, mtype2=0, mthr2=32, auxmthr=None):
	core = vs.get_core()
	
	#generate paramerters if None
	w = input.width
	h = input.height
	upw4 = (round(w*0.09375)*16) # mod16(w*1.5)
	uph4 = (round(h*0.09375)*16) # mod16(h*1.5)
	downw4 = (round(w*0.1875)*4) # mod4(w*0.75)
	downh4 = (round(h*0.1875)*4) # mod4(h*0.75)
	inputFormatid = input.format.id
	funcname = 'TAAmbk'
	
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
				
	if sharp == None:
		if preaa == -1:
			sharp = -1
		else:
			if preaa != 0:
				sharp = 0.3
			else:
				if aatype == 0:
					sharp = 0
				else:
					if aatype > 0 and aatype <= 3:
						sharp = 0.2
					else:
						sharp = 70
				
	absSh = abs(sharp)
	if postaa == None:
		if absSh > 70 or (absSh > 0.4 and absSh < 1):
			postaa = True
		else:
			postaa = False
			
	if aarepair == None:
		if predown:
			aarepair = 2
		else:
			aarepair = 0
	
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
	#				 aatype =	-3	    -2		-1		0	   1	  2      3		 4		 5		 6
	if p1	is None: p1		=	[	48,	    48,		48,		0,	   10,	 0.5, 	 3,		48,		48,		48][pindex]
	if p2	is None: p2		=	[	 3,	   0.5,		10,		0,	   20,	 0.2, 	 1,		 1,		 0,		rp][pindex]
	if p3	is None: p3		=	[	 1,	   0.2,		20,		0,	   20,	  20, 	 2,		 3,		 0,		 0][pindex]
	if p4	is None: p4		=	[	 2,	    20,		20,		0,	   24,	   3, 	 0,		 2,		 0,		 0][pindex]
	if p4	is None: p4		=	[	 2,	    20,		20,		0,	   24,	   3, 	 0,		 2,		 0,		 0][pindex]
	if p5	is None: p5		=	[	 0,	     3,		24,		0,	   50,	  30, 	 0,		 0,		 0,		 0][pindex]
	if p6	is None: p6		=	[	 0,	    30,		50,		0,	    0,	   0, 	 0,		 0,		 0,		 0][pindex]
	
	
	#paramerters check
	#input check
	if not isinstance(input, vs.VideoNode):
		raise ValueError(funcname + ': \"input\" must be a clip !')
	sColorFamily = input.format.color_family
	if sColorFamily == vs.YUV or sColorFamily == vs.GRAY:
		None
	else:
		raise ValueError(funcname + ': Only YUV colorfmaily is supported !')
	#aatype check
	if not isinstance(aatype, int) or (aatype < -3 or aatype > 6):
		raise ValueError(funcname + ': \"aatype\" (int: -3~6) invalid !')
	if not ignore and (aatype == -2 or aatype == 2):
		raise ValueError(funcname + ': \"aatype\" -2 or 2 seems to have something wrong, NOT available if \"ignore\" set to False !')
	#preaa check
	if not isinstance(preaa, int) or (preaa < -1 or preaa > 2):
		raise ValueError(funcname + ': \"preaa\" (int: -1~2) invalid !')
	#mtype check
	if not isinstance(mtype, int):
		if not isinstance(mtype, vs.VideoNode):
			raise TypeError(funcname + ': \"mtype\" is not a clip !')
		else:
			if mtype.format.id != inputFormatid :
				raise TypeError(funcname + ': \"input\" and \"mclip(mtype)\" must be of the same format !')
			else:
				if mtype.width != w or mtype.height != h:
					raise TypeError(funcname + ': resolution of \"input\" and \"mclip(mtype)\" must match !')
	else:
		if mtype < 0 or mtype > 6:
			raise ValueError(funcname + ': \"mtype\" (int: 0~6) invalid !')
	#mthr check
	if not isinstance(mthr, int) or (mthr < 0 or mthr > 255):
		raise ValueError(funcname + ': \"mthr\" (int: 0~255) invalid !')
	#aarepair check
	if not isinstance(aarepair, int) or (aarepair < 0 or aarepair > 24):
		raise ValueError(funcname + ': \"aarepair\" (int: 0~24) invalid !')
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
	#stablize check
	if not isinstance(stablize, int) or (stablize < 0 or stablize > 3):
		raise ValueError(funcname + ': \"stablize\" (int: 0~3) invalid !')
	if showmask and mtype == 0:
		raise ValueError(funcname + ': you can not show mask when mtype=0 !')
		
	###bugs
	if mtype == 5 or mtype2 == 5:
		raise ValueError(funcname + ': \"mtype\" or \"mtype2\" = 5 (Roberts) unavailable now !')
	
	
	# src clip issue
	#======================
	if src == None:
		if predown:
			src = core.nnedi3.nnedi3(core.fmtc.resample(input, w=downw4, h=downh4,kernel="spline36"),field=1,dh=True)
			src = core.std.Transpose(core.fmtc.resample(src,w=downw4,h=h,sx=0,sy=[-0.5,-0.5*(1<<input.format.subsampling_h)],kernel="spline36"))
			src = core.std.Transpose(core.fmtc.resample(core.nnedi3.nnedi3(src,field=1,dh=True),w=h,h=w,sx=0,sy=[-0.5,-0.5*(1<<input.format.subsampling_h)],kernel="spline36"))
		else:
			src = input
	#======================
	



	#average two clips of 3 yuv planes
	def average(clipa, clipb):
		return (core.std.Expr(clips=[clipa,clipb], expr=["x y + 2 /"]))
	
	#internal function
	def TAAmbk_prepass(clip, predown=predown, downw4=downw4, downh4=downh4, thin=0, dark=0, preaa=preaa):
		if predown:
			pdclip = core.resize.Spline(clip, downw4, downh4)
		else:
			pdclip = clip
		
		nn = core.nnedi3.nnedi3(pdclip, field=3)
		nnt = core.std.Transpose(core.nnedi3.nnedi3(core.std.Transpose(pdclip), field=3))
		#nnedi3 double rate start with top
		clph = average(core.std.SelectEvery(nn, cycle=2, offsets=0), core.std.SelectEvery(nn, cycle=2, offsets=1))
		clpv = average(core.std.SelectEvery(nnt, cycle=2, offsets=0), core.std.SelectEvery(nnt, cycle=2, offsets=1))
		clp = average(clph, clpv)
		if preaa == -1:
			preaaB = clp
		elif preaa == 1:
			preaaB = clph
		elif preaa == 2:
			preaaB = clpv
		else:
			preaaB = pdclip
		#filters unavailable
		#=======================================
		#if thin == 0 and dark == 0:
			#preaaC=preaaB
		
		#else:
			#preaaC=preaaB
		#=======================================
		preaaC = preaaB
		
		return preaaC
		
		
		
		
		
	#internal functions
	def TAAmbk_mainpass(preaaC, aatype=aatype, cycle=cycle, p1=p1, p2=p2, p3=p3, p4=p4, p5=p5, p6=p6, w=w, h=h,
						uph4=uph4, upw4=upw4, eedi3sclip=eedi3sclip):
						
		if eedi3sclip is True:
			if aatype == -2:
				sclip = core.nnedi3.nnedi3(preaaC,field=1,dh=True)
				sclip_r = core.resize.Spline(sclip,w,uph4)
				sclip_r = core.std.Transpose(sclip_r)
				sclip_r = core.nnedi3.nnedi3(sclip_r,field=1,dh=True)
				sclip = mvf.Depth(sclip,8)
				sclip_r = mvf.Depth(sclip_r,8)
			elif aatype == 2:
				sclip = core.nnedi3.nnedi3(preaaC,field=1,dh=True)
				sclip_r = sclip_r = core.resize.Spline(sclip,w,h)
				sclip_r = core.std.Transpose(sclip_r)
				sclip_r = core.nnedi3.nnedi3(sclip_r,field=1,dh=True)
				sclip = mvf.Depth(sclip,8)
				sclip_r = mvf.Depth(sclip_r,8)
			else:
				sclip = None
				sclip_r = None
		else:
			sclip = None
			sclip_r = None
		
		# generate aa_clip
		if aatype == -3 or aatype == 4:
			aa_clip = core.nnedi3.nnedi3(preaaC, dh=True, field=1, nsize=int(p2), nns=int(p3), qual=int(p4))
			aa_clip = core.std.Transpose(core.fmtc.resample(aa_clip,w=w,h=uph4,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36"))
			aa_clip = core.fmtc.resample(core.nnedi3.nnedi3(aa_clip, dh=True, field=1, nsize=int(p2), nns=int(p3), qual=int(p4)),w=uph4,h=upw4,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
			aa_clip = mvf.Depth(aa_clip,depth=8)
			aa_clip = core.sangnom.SangNomMod(core.std.Transpose(core.sangnom.SangNomMod(aa_clip,aa=int(p1))),aa=int(p1))
			aa_clip = core.fmtc.resample(aa_clip,w=w,h=h,kernel=["spline36","spline36"])
		else:
			if aatype == -2:
				if eedi3sclip == False:
					
					aa_clip = core.fmtc.resample(core.eedi3.eedi3(preaaC, dh=True, field=1, alpha=p2, beta=p3, gamma=p4, nrad=int(p5), mdis=int(p6)), w=w, h=uph4, sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
					aa_clip = mvf.Depth(aa_clip,depth=8)
					aa_clip = core.eedi3.eedi3(core.std.Transpose(aa_clip), dh=True, field=1, alpha=p2, beta=p3, gamma=p4, nrad=int(p5), mdis=int(p6))
					aa_clip = core.sangnom.SangNomMod(mvf.Depth(core.fmtc.resample(aa_clip, w=uph4, h=upw4, sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36"),depth=8),aa=int(p1))
					aa_clip = core.sangnom.SangNomMod(core.std.Transpose(aa_clip),aa=int(p1))
					aa_clip = core.fmtc.resample(aa_clip,w=w,h=h,kernel=["spline36","spline36"])
				else:
					# EEDI3 need w * h
					aa_clip = core.fmtc.resample(core.eedi3.eedi3(preaaC, dh=True, field=1, alpha=p2, beta=p3, gamma=p4, nrad=int(p5), mdis=int(p6), sclip=sclip), w=w, h=uph4, sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
					# output w * uph4
					aa_clip = mvf.Depth(aa_clip,depth=8)
					# EEDI3 need uph4 * w
					aa_clip = core.eedi3.eedi3(core.std.Transpose(aa_clip), dh=True, field=1, alpha=p2, beta=p3, gamma=p4, nrad=int(p5), mdis=int(p6), sclip=sclip_r)
					aa_clip = core.sangnom.SangNomMod(mvf.Depth(core.fmtc.resample(aa_clip, w=uph4, h=upw4, sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36"),depth=8),aa=int(p1))
					aa_clip = core.sangnom.SangNomMod(core.std.Transpose(aa_clip),aa=int(p1))
					aa_clip = core.fmtc.resample(aa_clip,w=w,h=h,kernel=["spline36","spline36"])
			else:
				if aatype == -1:
					aa_clip = core.fmtc.resample(core.eedi2.EEDI2(preaaC, field=1, mthresh=int(p2), lthresh=int(p3), vthresh=int(p4), maxd=int(p5), nt=int(p6)),w=w,h=uph4,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
					aa_clip = core.eedi2.EEDI2(core.std.Transpose(aa_clip),field=1, mthresh=int(p2), lthresh=int(p3), vthresh=int(p4), maxd=int(p5), nt=int(p6))
					aa_clip = core.sangnom.SangNomMod(mvf.Depth(core.fmtc.resample(aa_clip,w=uph4,h=upw4,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36"),depth=8),aa=int(p1))
					aa_clip = core.sangnom.SangNomMod(core.std.Transpose(aa_clip),aa=int(p1))
					aa_clip = core.fmtc.resample(aa_clip,w=w,h=h,kernel=["spline36","spline36"])
				else:
					if aatype == 1:
						aa_clip = core.fmtc.resample(core.eedi2.EEDI2(preaaC,field=1,mthresh=int(p1), lthresh=int(p2), vthresh=int(p3), maxd=int(p4), nt=int(p5)),w=w,h=h,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
						aa_clip = core.eedi2.EEDI2(core.std.Transpose(aa_clip),field=1,mthresh=int(p1), lthresh=int(p2), vthresh=int(p3), maxd=int(p4), nt=int(p5))
						aa_clip = core.std.Transpose(core.fmtc.resample(aa_clip,w=h,h=w,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36"))
					else:
						if aatype == 2:
							if eedi3sclip == False:
								aa_clip = core.fmtc.resample(core.eedi3.eedi3(preaaC,dh=True, field=1, alpha=p1, beta=p2, gamma=p3, nrad=int(p4), mdis=int(p5)),w=w,h=h,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
								aa_clip = mvf.Depth(core.std.Transpose(aa_clip),depth=8)
								aa_clip = core.fmtc.resample(core.eedi3.eedi3(aa_clip,dh=True, field=1, alpha=p1, beta=p2, gamma=p3, nrad=int(p4), mdis=int(p5)),w=h,h=w,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
								aa_clip = core.std.Transpose(aa_clip)
							else:
								#EEDI3 need w * h
								aa_clip = core.fmtc.resample(core.eedi3.eedi3(preaaC,dh=True, field=1, alpha=p1, beta=p2, gamma=p3, nrad=int(p4), mdis=int(p5), sclip=sclip),w=w,h=h,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
								#output w * h
								aa_clip = mvf.Depth(core.std.Transpose(aa_clip),depth=8)
								#EEDI3 need h * w
								aa_clip = core.fmtc.resample(core.eedi3.eedi3(aa_clip,dh=True, field=1, alpha=p1, beta=p2, gamma=p3, nrad=int(p4), mdis=int(p5), sclip=sclip_r),w=h,h=w,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
								aa_clip = core.std.Transpose(aa_clip)
						else:
							if aatype == 3:
								aa_clip = core.fmtc.resample(core.nnedi3.nnedi3(preaaC, dh=True, field=1, nsize=int(p1), nns=int(p2), qual=int(p3)),w=w,h=h,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
								aa_clip = core.nnedi3.nnedi3(core.std.Transpose(aa_clip), dh=True, field=1, nsize=int(p1), nns=int(p2), qual=int(p3))
								aa_clip = core.std.Transpose(core.fmtc.resample(aa_clip,w=h,h=w,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36"))
							else:
								if aatype == 5:
									aa_clip = mvf.Depth(core.fmtc.resample(preaaC, w=upw4, h=uph4 ,kernel=["lanczos","bicubic"]),depth=8)
									aa_clip = core.std.Transpose(core.sangnom.SangNomMod(aa_clip,aa=int(p1)))
									aa_clip = core.fmtc.resample(core.sangnom.SangNomMod(aa_clip,aa=int(p1)),w=h,h=w,kernel="spline36")
									aa_clip = core.std.Transpose(aa_clip)
								else:
									if aatype == 6:
										aa_clip = mvf.Depth(core.fmtc.resample(preaaC, w=w, h=uph4 ,kernel=["lanczos","bicubic"]),depth=8)
										aa_clip = core.fmtc.resample(core.sangnom.SangNomMod(aa_clip,aa=int(p1)),w=w,h=h,kernel="spline36")
										aa_clip = core.fmtc.resample(core.std.Transpose(aa_clip),w=h,h=upw4,kernel=["lanczos","bicubic"])
										aa_clip = core.sangnom.SangNomMod(mvf.Depth(aa_clip,depth=8),aa=int(p1))
										aa_clip = core.std.Transpose(core.fmtc.resample(aa_clip,w=h,h=w,kernel="spline36"))
										aa_clip = core.rgvs.Repair(aa_clip, mvf.Depth(preaaC,depth=16), mode=int(p2))
									else:
										if predown:
											aa_clip = core.fmtc.resample(core.nnedi3.nnedi3(preaaC,dh=True, field=1, nsize=1, nns=3, qual=2),w=preaaC.width,h=h,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36")
											aa_clip = core.nnedi3.nnedi3(core.std.Transpose(aa_clip),dh=True, field=1, nsize=1, nns=3, qual=2)
											aa_clip = core.std.Transpose(core.fmtc.resample(aa_clip,w=h,h=w,sx=0,sy=[-0.5,-0.5*(1<<preaaC.format.subsampling_h)],kernel="spline36"))
										else:
											aa_clip = preaaC
		
		return aa_clip if cycle == 0 else TAAmbk_mainpass(aa_clip, aatype=aatype ,cycle=cycle-1, p1=p1, p2=p2, p3=p3, p4=p4, p5=p5, p6=p6, w=w, h=h, uph4=uph4, upw4=upw4, eedi3sclip=eedi3sclip)
	
	
	
	
	#Internal functions
	def TAAmbk_mask(input, mtype=mtype, mthr=mthr, w=w, mtype2=mtype2, mthr2=mthr2, auxmthr=auxmthr):
	
		#generate edge_mask_1
		if mtype == 1:
			edge_mask_1 = core.tcanny.TCanny(input, sigma=auxmthr, mode=1, op=2, planes=0)
			exprY = "x "+str(mthr)+" <= x 2 / x 2 * ?"
			if input.format.num_planes == 1:
				edge_mask_1 = core.std.Expr(edge_mask_1, expr=[exprY])
			else:
				edge_mask_1 = core.std.Expr(edge_mask_1, expr=[exprY,""])
			if w > 1100:
				edge_mask_1 = core.rgvs.RemoveGrain(edge_mask_1, mode=20)
			else:
				edge_mask_1 = core.rgvs.RemoveGrain(edge_mask_1, mode=11)
			edge_mask_1 = core.generic.Inflate(edge_mask_1, planes=0)
		elif mtype == 3:
			edge_mask_1 = core.generic.TEdge(input, min=auxmthr, planes=0)
			exprY = "x "+str(mthr//5)+" <= x 2 / x 16 * ?"
			if input.format.num_planes == 1:
				edge_mask_1 = core.std.Expr(edge_mask_1, expr=[exprY])
			else:
				edge_mask_1 = core.std.Expr(edge_mask_1, expr=[exprY,""])
			edge_mask_1 = core.generic.Deflate(edge_mask_1, planes=0)
			if w > 1100:
				edge_mask_1 = core.rgvs.RemoveGrain(edge_mask_1, mode=20)
			else:
				edge_mask_1 = core.rgvs.RemoveGrain(edge_mask_1, mode=11)
		elif mtype == 2:
			edge_mask_1 = core.msmoosh.MSharpen(input, threshold=mthr//5, strength=0, mask=True, planes=0)
		elif mtype == 4:
			edge_mask_1 = core.generic.Sobel(input, min=5, max=7, planes=0)
			edge_mask_1 = core.generic.Inflate(edge_mask_1, planes=0)
		elif mtype == 5:
		#=======================
			edge_mask_1 = input # roberts kernel unavailable
			edge_mask_1 = core.generic.Inflate(edge_mask_1, planes=0)
		#=======================
		elif mtype == 6:
			edge_mask_1 = core.generic.Prewitt(input, min=0, max=255, planes=0)
			exprY = "x "+str(mthr)+" <= x 2 / x 2.639015821545 * ?"
			if input.format.num_planes == 1:
				edge_mask_1 = core.std.Expr(edge_mask_1, expr=[exprY])
			else:
				edge_mask_1 = core.std.Expr(edge_mask_1, expr=[exprY,""])
			edge_mask_1 = core.rgvs.RemoveGrain(edge_mask_1, mode=4)
			edge_mask_1 = core.generic.Inflate(edge_mask_1, planes=0)
		else:
			edge_mask_1 == None
			
		#generate edge_mask_2
		if mtype2 == 0:
			edge_mask_2 = None
		elif mtype2 == 1:
			edge_mask_2 = core.tcanny.TCanny(input, sigma=1.2, mode=1, op=0, planes=0)
			exprY = "x "+str(mthr2)+" <= x 2 / x 2 * ?"
			if input.format.num_planes == 1:
				edge_mask_2 = core.std.Expr(edge_mask_2, expr=[exprY])
			else:
				edge_mask_2 = core.std.Expr(edge_mask_2, expr=[exprY,""])
			if w > 1100:
				edge_mask_2 = core.rgvs.RemoveGrain(edge_mask_2, mode=20)
			else:
				edge_mask_2 = core.rgvs.RemoveGrain(edge_mask_2, mode=11)
			edge_mask_1 = core.generic.Inflate(edge_mask_2, planes=0)
		elif mtype2 == 3:
			edge_mask_2 = core.generic.TEdge(input, planes=0)
			exprY = "x "+str(mthr2//5)+" <= x 2 / x 16 * ?"
			if input.format.num_planes == 1:
				edge_mask_2 = core.std.Expr(edge_mask_2, expr=[exprY])
			else:
				edge_mask_2 = core.std.Expr(edge_mask_2, expr=[exprY,""])
			edge_mask_2 = core.generic.Deflate(edge_mask_2, planes=0)
			if w > 1100:
				edge_mask_2 = core.rgvs.RemoveGrain(edge_mask_2, mode=20)
			else:
				edge_mask_2 = core.rgvs.RemoveGrain(edge_mask_2, mode=11)
		elif mtype2 == 2:
			edge_mask_2 = core.msmoosh.MSharpen(input, threshold=mthr2//5, strength=0, mask=True, planes=0)
		elif mtype2 == 4:
			edge_mask_2 = core.generic.Sobel(input, min=5, max=7, planes=0)
			edge_mask_2 = core.generic.Inflate(edge_mask_2, planes=0)
		elif mtype2 == 5:
		#=======================
			edge_mask_2 = input
			edge_mask_2 = core.generic.Inflate(edge_mask_2, planes=0)
		#=======================
		elif mtype2 == 6:
			edge_mask_2 = core.generic.Prewitt(input, min=0, max=255, planes=0)
			exprY = "x "+str(mthr2)+" <= x 2 / x 2.639015821545 * ?"
			edge_mask_2 = core.std.Expr(edge_mask_2, expr=[exprY])
			edge_mask_2 = core.rgvs.RemoveGrain(edge_mask_2, mode=4)
			edge_mask_2 = core.generic.Inflate(edge_mask_2, planes=0)
		else:
			edge_mask_2 = None
			
		#generate final_mask
		if mtype2 == 0:
			final_mask = edge_mask_1
		else:
			final_mask = core.std.Expr(clips=[edge_mask_1,edge_mask_2], expr=["x y max"])
			
		return final_mask
	
	
	#temporal stabilizer of sharped clip
	def Soothe(sharp, origin, keep=24):
		if keep > 100:
			keep = 100
		if keep < 0:
			keep = 0
		KP = str(keep)
		diff = core.std.Expr(clips=[origin,sharp], expr=["x y - 128 +",""])
		diff2 = core.focus.TemporalSoften(diff, radius=1, luma_threshold=255, chroma_threshold=255, scenechange=32, mode=2)
		expr = "x 128 - y 128 - * 0 < x 128 - 100 / "+KP+" * 128 + x 128 - abs y 128 - abs > x "+KP+" * y 100 "+KP+" - * + 100 / x ? ?"
		diff3 = core.std.Expr(clips=[diff,diff2], expr=[expr,""])
		return core.std.Expr(clips=[origin,diff3], expr=["x y 128 - -",""])
		
	#internal functions
	def TAAmbk_postpass(aa_clip, input, absSh=absSh, src=src, postaa=postaa, stablize=stablize, limit=limit,
						mtype=mtype, mthr=mthr, showmask=showmask, sharp=sharp, w=w, mtype2=mtype2, mthr2=mthr2, 
						auxmthr=auxmthr, averagemask=averagemask):
		#postaaC
		if sharp == 0:
			postaaC = aa_clip
		elif sharp >= 1:
			postaaC = haf.LSFmod(aa_clip,strength=int(absSh), defaults="old", source=mvf.Depth(src,16))
		elif sharp > 0:
			per = int(40*absSh)
			matrix = [-1, -2, -1, -2, 52-per , -2, -1, -2, -1]
			postaaC = core.generic.Convolution(aa_clip,matrix,planes=0)
		elif sharp > -1:
			postaaC = haf.LSFmod(aa_clip,strength=round(absSh*100), defaults="fast", source=mvf.Depth(src,16))
		elif sharp == -1:
			if w > 1100:
				clipb = core.std.MakeDiff(aa_clip, core.rgvs.RemoveGrain(aa_clip, mode=20))
			else:
				clipb = core.std.MakeDiff(aa_clip, core.rgvs.RemoveGrain(aa_clip, mode=11))
			clipb = core.rgvs.Repair(clipb, core.std.MakeDiff(src, aa_clip),mode=13)
			postaaC = core.std.MergeDiff(aa_clip, clipb)
		else:
			postaaC = haf.LSFmod(aa_clip,strength=int(absSh), defaults="slow", source=mvf.Depth(src,16))
		
		if postaa:
			postaaC = Soothe(postaaC,aa_clip,keep=48)
		else:
			postaaC = postaaC
			
		if isinstance(mtype, vs.VideoNode):
			edge_mask = mtype
			aaed = core.std.MaskedMerge(mvf.Depth(input,16),postaaC,mvf.Depth(edge_mask,16),first_plane=True)
		else:
			if mtype == 0:
				edge_mask = None
				aaed = postaaC
			else:
				if averagemask:
					edge_mask = TAAmbk_mask(average(mvf.Depth(input,16),postaaC),mtype=mtype,mthr=mthr,w=w,mtype2=mtype2,mthr2=mthr2,auxmthr=auxmthr)
				else:
					edge_mask = TAAmbk_mask(input,mtype=mtype,mthr=mthr,w=w,mtype2=mtype2,mthr2=mthr2,auxmthr=auxmthr)
				aaed = core.std.MaskedMerge(mvf.Depth(input,16),postaaC,mvf.Depth(edge_mask,16),first_plane=True)
		
		if stablize == 0:
			aadiff = None
			inputsuper = None
			diffsuper = None
		else:
			aadiff = core.std.MakeDiff(mvf.Depth(input,16), aaed)
			inputsuper = core.mv.Super(input,pel=1)
			diffsuper = core.mv.Super(aadiff,pel=1,levels=1)
			
		if stablize == 3:
			fv3 = core.mv.Analyse(inputsuper,isb=False,delta=3,overlap=8,blksize=16)
		else:
			fv3 = None
		if stablize >= 2:
			fv2 = core.mv.Analyse(inputsuper,isb=False,delta=2,overlap=8,blksize=16)
		else:
			fv2 = None
		if stablize >= 1:
			fv1 = core.mv.Analyse(inputsuper,isb=False,delta=1,overlap=8,blksize=16)
		else:
			fv1 = None
		if stablize >= 1:
			bv1 = core.mv.Analyse(inputsuper,isb=True,delta=1,overlap=8,blksize=16)
		else:
			bv1 = None
		if stablize >= 2:
			bv2 = core.mv.Analyse(inputsuper,isb=True,delta=2,overlap=8,blksize=16)
		else:
			bv2 = None
		if stablize == 3:
			bv3 = core.mv.Analyse(inputsuper,isb=True,delta=3,overlap=8,blksize=16)
		else:
			bv3 = None
		if stablize == 1:
			stablized_diff = core.mv.Degrain1(aadiff,diffsuper,bv1,fv1)
		else:
			if stablize == 2:
				stablized_diff = core.mv.Degrain2(aadiff,diffsuper,bv1,fv1,bv2,fv2)
			else:
				if stablize == 3:
					stablized_diff = core.mv.Degrain3(aadiff,diffsuper,bv1,fv1,bv2,fv2,bv3,fv3)
				else:
					stablized_diff = None		
		
		if stablize == 0:
			stablized_diff2 = None
			aafinal = aaed
		else:
			stablized_diff2 = core.std.Expr(clips=[aadiff,stablized_diff], expr=["x 128 - abs y 128 - abs < x y ?"])
			if stablized_diff2.format.num_planes == 1:
				stablized_diff2 = core.std.Merge(stablized_diff2, stablized_diff, weight=[0.6])
			else:
				stablized_diff2 = core.std.Merge(stablized_diff2, stablized_diff, weight=[0.6,0])
			aafinal = core.std.MakeDiff(mvf.Depth(input,16), stablized_diff2, planes=0)
		
		if limit:
			aadiff2 = core.std.MakeDiff(mvf.Depth(input,16), aafinal)
			aasuper = core.mv.Super(aadiff2,pel=1)
			bv = core.mv.Analyse(aasuper,isb=True,overlap=8,blksize=16)
			fv = core.mv.Analyse(aasuper,isb=False,overlap=8,blksize=16)
			bc = core.mv.Compensate(aadiff2,aasuper,bv)
			fc = core.mv.Compensate(aadiff2,aasuper,fv)
			max_limit = core.std.Expr(clips=[aadiff2,bc], expr=["x y max"])
			max_limit = core.std.Expr(clips=[max_limit,fc], expr=["x y max"])
			min_limit = core.std.Expr(clips=[aadiff2,bc], expr=["x y min"])
			min_limit = core.std.Expr(clips=[max_limit,fc], expr=["x y min"])
			#diffclamp = core.generic.Limiter(aadiff2, min=min_limit, max=max_limit, planes=0)
			exprMax = "x y > y x ?"
			exprMin = "x y < y x ?"
			if aadiff2.format.num_planes == 1:
				diffclamp = core.std.Expr(clips=[aadiff2,max_limit], expr=[exprMax])
				diffclamp = core.std.Expr(clips=[diffclamp,min_limit], expr=[exprMin])
			else:
				diffclamp = core.std.Expr(clips=[aadiff2,max_limit], expr=[exprMax,""])
				diffclamp = core.std.Expr(clips=[diffclamp,min_limit], expr=[exprMin,""])
			aalimited = core.std.MakeDiff(mvf.Depth(input,16), diffclamp,planes=0)
		else:
			aadiff2 = None
			aasuper = None
			bv = None
			fv = None
			bc = None
			fc = None
			max_limit = None
			min_limit = None
			diffclamp = None
			aalimited = aafinal
			
		return edge_mask if showmask else aalimited
	
	#main functions
	preaaC = TAAmbk_prepass(input, predown=predown, downw4=downw4, downh4=downh4, preaa=preaa)
	
	aa_clip = TAAmbk_mainpass(preaaC,aatype=aatype, cycle=cycle, p1=p1, p2=p2, p3=p3, p4=p4, p5=p5, p6=p6, w=w, h=h, uph4=uph4, upw4=upw4, eedi3sclip=eedi3sclip)
	
	aalimited = TAAmbk_postpass(aa_clip,input,absSh=absSh,src=src,postaa=postaa,stablize=stablize,limit=limit,mtype=mtype,mthr=mthr,showmask=showmask,sharp=sharp,w=w,mtype2=mtype2,mthr2=mthr2,auxmthr=auxmthr,averagemask=averagemask)
	
	if showmask:
		return aalimited
	else:
		if aarepair == 0:
			return aalimited
		else:
			return core.rgvs.Repair(aalimited, mvf.Depth(input,depth=16), mode=aarepair)
