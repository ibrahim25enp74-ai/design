# Arabic typography

## Choosing fonts

Cairo, Tajawal and Almarai appear everywhere. They are good fonts, but choosing them by default is a big part of why Arabic designs look alike. Use them only on purpose.

Choose by voice (all of these are free on Google Fonts):

| Voice | Fonts |
|---|---|
| Geometric or Kufi, contemporary | Noto Kufi Arabic, Reem Kufi, Kufam, Readex Pro, Alexandria, Zain |
| Neutral sans for text and UI | IBM Plex Sans Arabic, Noto Sans Arabic, Vazirmatn, Mada |
| Naskh for reading and editorial weight | Amiri, Noto Naskh Arabic, Markazi Text, Scheherazade New |
| Display, one word or line at a time | Aref Ruqaa, Rakkas, Lalezar, Marhey, Blaka, El Messiri |

For a brand with a budget, retail Arabic fonts from foundries such as 29LT or Boutros set the work apart further.

**Pairing with Latin**: a family that covers both scripts is the safest choice (IBM Plex Sans Arabic with IBM Plex Sans, Noto Kufi Arabic with Noto Sans, Readex Pro). Otherwise, match the stroke weight and the visual size by eye, not the point size.

## Setting

- **Size**: at the same point size Arabic looks smaller than Latin. Set it 15–20% larger, or match the two by eye.
- **Line height**: 1.6–1.9 for running text, because the dots and the descending tails need room. Go tighter only for single-line display text.
- **Tracking**: never letterspace Arabic, because it breaks the joins. To widen, use weight or size. Use kashida (ـ) only in display lettering, placed by hand and sparingly.
- **Styles**: no fake italic or oblique, and no fake bold. Use real weights.
- **Alignment**: avoid justified Arabic in narrow columns unless the renderer does proper kashida justification. Ragged-left text (aligned right) is the safer choice.
- **Tashkeel**: add diacritics only where they are needed for meaning or as calligraphic display, and check they don't collide with the line above.

## Direction and layout

- **RTL**: reading starts at the top right, so the hierarchy should start there too. "Next" arrows point left. Mirror any layout designed for LTR, including carousel progress cues.
- **Mixed lines**: when Arabic, Latin and numbers share a line, check the order visually. The bidi algorithm often misplaces punctuation and numbers.
- **Numerals**: choose Arabic-Indic (٠١٢٣) or Western (0123) for each piece and stay consistent. In drawings, dimensions and sheet numbers conventionally use Western digits. Arabic posts can use either, consistently.

## Rendering Arabic from code

- The ezdxf drawing add-on, standard matplotlib, and Pillow without libraqm do not shape Arabic, so letters come out disconnected and in left-to-right order. Two fixes:
  - Render with a shaping engine (HarfBuzz): Pillow built with libraqm, a browser, Inkscape, or Cairo/Pango.
  - Or pre-process the string with `arabic_reshaper` plus `python-bidi` before handing it to a non-shaping renderer. Never pre-process for a renderer that already shapes, or the text gets reversed twice.
- In DXF, Arabic needs a text style mapped to a TTF that contains Arabic glyphs. SHX fonts won't render it.
- Look at every Arabic string in the final PDF or PNG and check for disconnected letters, reversed order, missing glyphs (boxes), and a correct lam-alef ligature (لا).
