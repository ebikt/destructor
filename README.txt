Destruktor
==========

Automatické klikadlo na instructor.cz


do_courses.py
-------------

Závislost: mechanicalsoup (apt install python3-mechanicalsoup)

Pokusí se vyplnit nesplněné kurzy.
(Stahování certifikátu není po změnách automatizované, protože na stránkách
instructor.cz přibyla možnost podepisování.)

Bez parametrů se zeptá na jméno a heslo:

  ./do_course.py

S prvním argumentem pass spustí zx2c4 pass na získání jména a hesla:

  ./do_courses.py pass my_password_path

ve skutečnosti prostě spustí `pass my_password_path` a očekává výstup ve formátu:

  heslo
  user: jmeno


sign.py
-------

Závislosti: bs4, pdfrw, pdftotext (apt install python3-bs4 python3 pdfrw poppler-utils)

Očekává pdf s certikátem, oříznuté pdf s podpisem, prefix výstupu:

  ./sign.py certificate.pdf signature.pdf output-prefix. [no]

Zapíše výstup do output-prefix.certificate.pdf. Pokud je čtvrtým parametrem "no",
tak bude podpis vložen "přes" text, normálně je vložen "pod" text (to je lepší,
když je podpis netransparentní).
