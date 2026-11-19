import io
p = r"D:\3dsg_1\research\code\scripts\occlusion_bound.py"
s = io.open(p, encoding="utf-8").read()
s = s.replace('''    hidden = torch.zeros(M, dtype=torch.bool, device=alpha.device)
    idx = torch.nonzero(sat).flatten()
    if idx.numel():
        # first saturated position per tile
        first = torch.ones(M, dtype=torch.bool, device=alpha.device)
        first[1:] = tile_ids[1:] != tile_ids[:-1]
        sat_first = sat & first.repeat_interleave(counts).bool()
        # simpler: for each entry, hidden if any earlier entry in same tile saturated
        csum = torch.cumsum(sat.long(), 0)
        before = csum - sat.long()
        base_sat = torch.repeat_interleave(before[start], counts)
        hidden = (before - base_sat) > 0''',
'''    # an entry is hidden if some EARLIER entry of the same tile already saturated
    csum = torch.cumsum(sat.long(), 0)
    before = csum - sat.long()
    base_sat = torch.repeat_interleave(before[start], counts)
    hidden = (before - base_sat) > 0''')
io.open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("fixed hidden computation")
