from app.parser.hybrid_parser import HybridParser

logs = """081109 203615 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_38865049064139660 terminating
081109 203616 149 INFO dfs.DataNode$PacketResponder: PacketResponder 2 for block blk_38865049064139661 terminating"""

p = HybridParser()
r = p.parse(logs)
print('parsed', len(r.parsed_logs))
print('templates', len(r.templates))
print('llm_calls', r.llm_calls)
print('new_templates', r.new_templates)
print(r.parsed_logs[0])
