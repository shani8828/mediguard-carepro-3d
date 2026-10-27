set -e
cd /home/claude
python3 make_screen.py out
python3 build_mesh.py out
python3 render.py out
rm -f out/_meshes.npy
python3 - <<'PY'
import medi_model as M
s=open('screen_ui.py').read(); m=open('medi_model.py').read().split('if __name__ == "__main__":')[0]
open('out/MediGuard_CarePro_C.FCMacro','w').write(s+"\n"+m+open('freecad_builder.py').read())
u=M.SLANT_LEN/2; cy=u*M.SLANT_D/M.SLANT_LEN+M.NY*2.5; cz=M.STACK_Z1+u*M.HDR_H/M.SLANT_LEN+M.NZ*2.5
t=open('viewer_template.html').read().replace('__SC__',f'{M.SCREEN_X},{cy:.2f},{cz:.2f}').replace('__SN__',f'0,{M.NY:.4f},{M.NZ:.4f}')
open('out/mediguard_viewer.html','w').write(t.replace('__DATA__',open('out/model.json').read()))
PY
cd /tmp/claude-0/stub && PYTHONPATH=. python3 /home/claude/out/MediGuard_CarePro_C.FCMacro | tail -1
