# Composite a Star Wars-style poster from six images
tfrom PIL import Image, ImageEnhance, ImageDraw, ImageFont

# Load images
map_bg = Image.open('/mnt/data/states.png').convert('RGBA')
mcmahon = Image.open('/mnt/data/Andrew-mcmahon.jpeg').convert('RGBA')
brandnew = Image.open('/mnt/data/brand-new-2.jpg').convert('RGBA')
menzingers = Image.open('/mnt/data/menzingers.jpeg').convert('RGBA')
deathcab = Image.open('/mnt/data/postal-service.jpg').convert('RGBA')
brandnew_poster = Image.open('/mnt/data/236299-brand-new-gloria-deja-entendu-album-covers-3923744739.jpg').convert('RGBA')

# Create canvas
width, height = 800, 1200
canvas = Image.new('RGBA', (width, height), (0, 0, 0, 255))

# Prepare background map
map_bg = map_bg.resize((width, height))
map_bg.putalpha(80)  # semi-transparent
canvas.paste(map_bg, (0, 0), map_bg)

# Prepare and paste Death Cab (center)
dc = deathcab.resize((500, 500))
x_dc = (width - dc.width) // 2
canvas.paste(dc, (x_dc, 200), dc)

# Paste Andrew McMahon (top left)
mc = mcmahon.resize((300, 300))
canvas.paste(mc, (50, 50), mc)

# Paste Brand New band (top right)
bn = brandnew.resize((300, 300))
canvas.paste(bn, (width - 350, 50), bn)

# Paste The Menzingers (bottom left)
men = menzingers.resize((300, 300))
canvas.paste(men, (50, height - 350), men)

# Paste Brand New poster/logo (bottom right)
bnp = brandnew_poster.resize((300, 300))
canvas.paste(bnp, (width - 350, height - 350), bnp)

# Add Star Wars-style text
draw = ImageDraw.Draw(canvas)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
draw.text((width // 2 - 150, height - 100), "A NEW HOPE IN MUSIC", font=font, fill=(255, 215, 0, 255))

# Save composite
output_path = '/mnt/data/star_wars_poster.png'
canvas.save(output_path)
print(f"Poster saved to {output_path}")

