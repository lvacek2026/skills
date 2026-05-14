# Smluvní závazky a předčasné ukončení smlouvy

Detailní reference k pravidlům pro smlouvy na dobu určitou u služeb
elektronických komunikací v ČR. Stav vychází z novely zákona č. 127/2005 Sb.
o elektronických komunikacích účinné od 1. 4. 2020 a pozdějších úprav;
ověřeno k roku 2026.

## Obsah
1. Sankce za předčasné ukončení smlouvy na dobu určitou
2. Práh tří měsíců
3. Zařízení poskytnuté za zvýhodněných podmínek
4. Maximální délka závazku
5. Na koho se pravidla vztahují
6. Praktické důsledky pro ISP

## 1. Sankce za předčasné ukončení smlouvy na dobu určitou

Před 1. 4. 2020 mohl operátor při předčasném ukončení smlouvy na dobu určitou
účtovat smluvní pokutu až 20 % (jedna pětina) součtu paušálů zbývajících do
konce závazku.

Novelou účinnou od 1. 4. 2020 se to zásadně změnilo:

- Pokud smlouva skončí **do 3 měsíců** od uzavření, smí operátor požadovat
  úhradu nejvýše **jednu dvacetinu (5 %)** součtu měsíčních paušálů nebo
  minimálních sjednaných měsíčních plnění zbývajících do konce sjednané doby
  trvání smlouvy.
- Pokud smlouva skončí **po uplynutí prvních 3 měsíců**, operátor za předčasné
  ukončení **nesmí účtovat žádnou smluvní pokutu**.

Výše úhrady se vždy počítá z částky placené v průběhu trvání smlouvy.

Tato úprava (§ 63 zákona o elektronických komunikacích) se vztahuje i na
smlouvy uzavřené před účinností novely — není to jen pravidlo o tom, co má být
nově ve smlouvě, ale zásah do obsahu existujících smluv.

## 2. Práh tří měsíců

Tří měsíce jsou klíčový předěl. Drtivá většina zákazníků uvažujících o přechodu
je u svého operátora déle než 3 měsíce — pro ně je sankce za předčasné ukončení
nulová. Jen čerstvě nasmlouvaný zákazník (méně než 3 měsíce) řeší onu 5%
úhradu.

Důsledek pro argumentaci: tvrzení "ze závazku se dostanete bez sankce" je pro
naprostou většinu lidí pravdivé, ale vždy ho podmiň "pokud jste u operátora
déle než 3 měsíce", aby bylo přesné i pro tu menšinu.

## 3. Zařízení poskytnuté za zvýhodněných podmínek

Omezení sankce se NEvztahuje na úhradu nákladů spojených s telekomunikačním
koncovým zařízením, které bylo účastníkovi poskytnuto za zvýhodněných podmínek
— typicky mobilní telefon, modem nebo router pořízený se slevou nebo na
splátky.

Pokud zákazník takové zařízení má:
- musí doplatit rozdíl mezi zvýhodněnou a plnou (katalogovou) cenou, případně
  zbývající splátky;
- tato povinnost trvá i po prvních 3 měsících, nezávisle na sankci za ukončení
  služby;
- jde-li o úvěr na zařízení (samostatná úvěrová smlouva), řídí se navíc
  pravidly pro spotřebitelský úvěr a zákazník se z něj nevyváže ukončením
  telekomunikační služby.

Praktická poznámka: zařízení na splátky bývá vendor-locked — nakonfigurované
tak, že nefunguje na síti jiného poskytovatele. Zákazník tedy platí za kus
hardwaru, který nemůže dál používat. To ho motivuje nepřecházet; ISP s tím nic
neudělá, ale měl by na to zákazníka upozornit dopředu a poctivě.

## 4. Maximální délka závazku

Smlouva na dobu určitou smí být uzavřena nejvýše na 24 měsíců. Operátor musí
zároveň nabízet možnost uzavřít smlouvu s dobou trvání nejvýše 12 měsíců.

Automatické prodlužování smlouvy na dobu určitou do dalšího období na dobu
určitou není přípustné tak, aby zákazníka znovu zavázalo — po uplynutí sjednané
doby se smlouva mění na dobu neurčitou (s možností výpovědi), pokud se strany
nedohodnou jinak.

## 5. Na koho se pravidla vztahují

Ochrana se vztahuje na **spotřebitele** a na **podnikající fyzické osoby**
(živnostníky, IČO fyzické osoby). Před novelou měli živnostníci horší postavení
— museli při předčasném ukončení doplatit celou zbývající částku; nově mají
stejné podmínky jako spotřebitelé.

Pozor: na právnické osoby (s.r.o., a.s.) se tato ochrana NEvztahuje. Ty v
případě předčasného ukončení musí typicky doplatit celou zbývající částku do
konce závazku podle smluvních podmínek.

## 6. Praktické důsledky pro ISP

Pro menšího ISP, který získává zákazníky od konkurence, z toho plyne:

Závazek u konkurence je pro akvizici slabá překážka — pro většinu zákazníků
fakticky neexistuje. To je silný argument, ale musí se podávat přesně.

Vlastní závazek: ISP smí dát závazek max. 24 měsíců, ale i ten je pro zákazníka
"měkký" — po 3 měsících z něj může odejít bez sankce. Závazek tedy reálně
nedrží zákazníka; co ho drží, je spokojenost se službou. Marketingově proto
dává smysl jít spíš cestou "bez závazku" jako benefitu než stavět na vázání.

Pokud ISP dává zákazníkovi zařízení (router) ZDARMA — tedy ne na splátky, ne za
zvýhodněnou cenu s doplatkem — pak nevzniká povinnost nic doplácet a je férové
to tak i komunikovat. Jakmile by šlo o "zvýhodněnou cenu" nebo splátky, spadá
to do režimu podle bodu 3.
