import matplotlib.font_manager as fm

for font_path in fm.findSystemFonts(fontpaths=None, fontext='ttf'):
    try:
        font_prop = fm.FontProperties(fname=font_path)
        font_name = font_prop.get_name()
        print(font_name)
    except Exception as e:
        continue  # 読み込みに失敗したフォントはスキップ