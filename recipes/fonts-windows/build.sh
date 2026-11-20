d="$DESTDIR/usr/share/fonts/truetype/fonts-windows"
install -d "$d"
find . -type f \( -iname '*.ttf' -o -iname '*.ttc' -o -iname '*.otf' \) | sort | while IFS= read -r f; do
	name=$(basename "$f")
	install -m644 "$f" "$d/$name"
	fam=$(fc-query -f '%{family}\n' "$d/$name" 2>/dev/null) || { rm -f "$d/$name"; continue; } # not a font
	case $name in *.[tT][tT][cC]) continue ;; esac # collections: none of these families
	# Their Arabic is too small: removed, so Vazirmatn draws it. dovy check
	# names the same families.
	if printf '%s\n' "$fam" | tr ',' '\n' | grep -qxE 'Arial|Times New Roman|Courier New|Calibri|Microsoft Sans Serif|Tahoma|Segoe UI' &&
		fc-query -f '%{lang}\n' "$d/$name" | tr '|' '\n' | grep -qx ar; then
		hb-subset "$d/$name" -o "$d/.stripped" \
			--unicodes='*' --unicodes-=600-6FF,750-77F,870-8FF,FB50-FDFF,FE70-FEFF \
			--layout-features='*' --name-IDs='*' --name-languages='*' \
			--notdef-outline --glyph-names --retain-gids --passthrough-tables
		mv "$d/.stripped" "$d/$name"
	fi
done
[ -n "$(ls -A "$d")" ] || { echo "no fonts in the folder" >&2; exit 1; }
