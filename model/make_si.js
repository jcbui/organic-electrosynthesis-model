// Build the Section 4 Supporting Information document.
//
// BUILD COMMAND (from anywhere):   node "<repo>/make_si.js"
// Canonical output:                <repo>/SI_Section4_Transport_Model.docx
// Inputs:                          <repo>/data/reactions_50.csv
//                                  <repo>/data/parameters_provenance.csv
//
// Every path below is resolved from __dirname, NOT from the working directory. It used to read its
// two CSVs by bare relative name and write its .docx into the cwd, so `cd data && node ../make_si.js`
// was the only invocation that worked and it deposited the document in data/ — while the repo root
// held SI_Section4_Transport_Model_v3.docx, which this build never updated. Two SI documents existed,
// one stale, neither obviously canonical. There is now exactly one output path and the cwd cannot
// change it; the v3 file has been retired to _archive/ (see docs/ARCHIVE_MANIFEST.md).
const fs = require("fs");
const path = require("path");
const ROOT = __dirname;
const DATA = path.join(ROOT, "data");
const RX_CSV = path.join(DATA, "reactions_50.csv");
const PROV_CSV = path.join(DATA, "parameters_provenance.csv");
// SI_MODE=condensed builds the pre-review SI from THIS generator: the same elements, filtered by the
// explicit plan in data/si_condensed_plan.json. Nothing is written for the condensed build that the
// detailed build does not also print, so the two documents cannot disagree on a number.
const SI_MODE = process.env.SI_MODE === "condensed" ? "condensed" : "detailed";
const OUT_DOCX = path.join(ROOT, SI_MODE === "condensed"
  ? "SI_Section4_Transport_Model_condensed.docx" : "SI_Section4_Transport_Model.docx");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow,
  TableCell, WidthType, BorderStyle, PageOrientation, ShadingType, LevelFormat, PageBreak,
  Math: OMath, MathRun, MathFraction, MathRadical, MathSubScript, MathSuperScript, MathSum,
  MathRoundBrackets, MathSquareBrackets, MathFunction, TabStopType, TableLayoutType, ImageRun } = require("docx");

// ---------- RSC-style numbered references ----------
// REFS order == citation numbers (order of first appearance in the document; enforced by auditRefOrder()).
// Journal helper: authors, italic journal, year, bold volume (null for no-volume/DOI-only), pages/article no.
const J = (a, j, y, v, pg) => [{ t: a + ", " }, { t: j, i: true }, { t: ", " + y + ", " },
  ...(v !== null ? [{ t: String(v), b: true }, { t: ", " }] : []), { t: pg + "." }];

// The eleven class shares, read from the stratification's own artifact rather than typed. They had
// gone stale once: correcting row 11's class on 2026-10-05 moved two of them while G-STRAT passed,
// because that gate checks the paragraph's five CLAIMS and never the share list.
const STRAT = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "khl_stratification.json"), "utf8"));
const STRAT_NAME = {
  "Cyclization": "cyclization", "C-C formation": "C\u2013C formation", "C-N formation": "C\u2013N formation",
  "Functional group intraconversion": "functional-group intraconversion",
  "Other bond formation": "other bond formation", "Multicomponent coupling": "multicomponent coupling",
  "C-O formation": "C\u2013O formation", "Oxidation": "oxidation", "C-S formation": "C\u2013S formation",
  "Reduction": "reduction", "Halogenation": "halogenation",
};
function stratShares() {
  const parts = STRAT.shares.map(r => {
    const nm = STRAT_NAME[r.cls];
    if (!nm) throw new Error("no SI display name for stratification class " + r.cls);
    return nm + " " + r.set_pct.toFixed(1) + "% vs " + r.corpus_pct.toFixed(1) + "%";
  });
  return parts.slice(0, -1).join(", ") + " and " + parts[parts.length - 1];
}

const REFS = [
  { k: "bui2022",       s: J("J. C. Bui, E. W. Lees, L. M. Pant, I. V. Zenyuk, A. T. Bell and A. Z. Weber", "Chem. Rev.", 2022, 122, "11022–11084") },
  { k: "oliver2025",    s: J("Z. J. Oliver et al.", "ACS Cent. Sci.", 2025, 11, "528–538") },
  { k: "bard",          s: [{ t: "A. J. Bard and L. R. Faulkner, " }, { t: "Electrochemical Methods: Fundamentals and Applications", i: true }, { t: ", John Wiley & Sons, New York, 2nd edn, 2001." }] },
  { k: "watkins2023",   s: J("N. B. Watkins, Z. J. Schiffer, Y. Lai, C. B. Musgrave III, H. A. Atwater, W. A. Goddard III, T. Agapie, J. C. Peters and J. M. Gregoire", "ACS Energy Lett.", 2023, 8, "2185–2192") },
  { k: "mo2020",        s: J("Y. Mo, Z. Lu, G. Rughoobur, P. Patil, N. Gershenfeld, A. I. Akinwande, S. L. Buchwald and K. F. Jensen", "Science", 2020, 368, "1352–1357") },
  { k: "levich",        s: [{ t: "V. G. Levich, " }, { t: "Physicochemical Hydrodynamics", i: true }, { t: ", Prentice-Hall, Englewood Cliffs, NJ, 1962." }] },
  { k: "eisenberg",     s: J("M. Eisenberg, C. W. Tobias and C. R. Wilke", "J. Electrochem. Soc.", 1954, 101, "306–320") },
  { k: "wilke1955",     s: J("C. R. Wilke and P. Chang", "AIChE J.", 1955, 1, "264–270") },
  { k: "poling",        s: [{ t: "B. E. Poling, J. M. Prausnitz and J. P. O'Connell, " }, { t: "The Properties of Gases and Liquids", i: true }, { t: ", McGraw-Hill, New York, 5th edn, 2001." }] },
  { k: "crc",           s: [{ t: "CRC Handbook of Chemistry and Physics", i: true }, { t: ", ed. W. M. Haynes, CRC Press, Boca Raton, FL, 97th edn, 2016." }] },
  { k: "izutsu",        s: [{ t: "K. Izutsu, " }, { t: "Electrochemistry in Nonaqueous Solutions", i: true }, { t: ", Wiley-VCH, Weinheim, 2nd edn, 2009." }] },
  { k: "ruecker2024",   s: J("T. Rücker, T. Pettersen, H. Graute, B. Wittgens, T. Graßl and S. R. Waldvogel", "ACS Sustainable Chem. Eng.", 2024, 12, "11283–11296") },
  { k: "peters2019",    s: J("B. K. Peters et al.", "Science", 2019, 363, "838–845") },
  { k: "jang2022",      s: J("J. Jang, M. Rüscher, M. Winzely and C. G. Morales-Guio", "AIChE J.", 2022, 68, "e17605") },
  { k: "lehnherr2024",  s: J("D. Lehnherr and L. Chen", "Org. Process Res. Dev.", 2024, 28, "338–366") },
  { k: "kelly2026",     s: J("M. Kelly, L. Cardinale, K. V. Sackett, S. Zhang, G. L. Beutner, B. Cohen, S. S. Stahl and M. Schreier", "Org. Process Res. Dev.", 2026, 30, "1926\u20131936") },
  { k: "ferretti2025",  s: J("A. C. Ferretti, B. Cohen, L. Deng, M. Diwan, M. O. Frederick and D. Lehnherr", "Org. Process Res. Dev.", 2025, 29, "322–332") },
  { k: "yang2023nc",    s: J("D. Yang, Z. Guan, Y. Peng, S. Zhu, P. Wang, Z. Huang, H. Alhumade, D. Gu, H. Yi and A. Lei", "Nat. Commun.", 2023, 14, "1476") },
  { k: "chien2025",     s: J("P.-C. Chien, F. A. Breitschaft, H. Kelm, S. R. Waldvogel and G. Manolikakes", "ChemSusChem", 2025, 18, "e202500186") },
  { k: "mei2019",       s: J("H. Mei, J. Liu, Y. Guo and J. Han", "ACS Omega", 2019, 4, "14353–14359") },
  { k: "baizer1964",    s: J("M. M. Baizer", "J. Electrochem. Soc.", 1964, 111, "215–222") },
  { k: "us5507922",     s: [{ t: "D. Hermeling, H. Hannebaum, H. Voss and A. Weiper-Idelmann (BASF AG), US Pat., 5507922, 1996." }] },
  { k: "bottecchia2022",s: J("C. Bottecchia et al.", "Org. Process Res. Dev.", 2022, 26, "2423–2437") },
  { k: "shono1975",     s: J("T. Shono, H. Hamaguchi and Y. Matsumura", "J. Am. Chem. Soc.", 1975, 97, "4264–4268") },
  { k: "puetter2001",   s: [{ t: "H. Pütter, in " }, { t: "Organic Electrochemistry", i: true }, { t: ", ed. H. Lund and O. Hammerich, Marcel Dekker, New York, 4th edn, 2001, ch. 31, pp. 1259–1308." }] },
  { k: "ep0011712",     s: [{ t: "D. Degner, M. Barl and H. Siegel (BASF AG), Eur. Pat. Appl., EP0011712A2, 1980." }] },
  { k: "us8629304",     s: [{ t: "F. Stecker, A. Fischer, J. Botzem, U. Griesbach and R. Pelzer (BASF SE), US Pat., 8629304, 2014." }] },
  { k: "leow2020",      s: J("W. R. Leow et al.", "Science", 2020, 368, "1228–1233") },
  { k: "kawamata2019",  s: J("Y. Kawamata et al.", "J. Am. Chem. Soc.", 2019, 141, "6392–6402") },
  { k: "liu2025",       s: J("Y. Liu, Y. Sun, Y. Deng and Y. Qiu", "Angew. Chem., Int. Ed.", 2025, 64, "e202504459") },
  { k: "deprez2021",    s: J("N. R. Deprez, D. J. Clausen, J.-X. Yan, F. Peng, S. Zhang, J. Kong and Y. Bai", "Org. Lett.", 2021, 23, "8834–8837") },
  { k: "zhao2021",      s: J("H.-B. Zhao, J.-L. Zhuang and H.-C. Xu", "ChemSusChem", 2021, 14, "1692–1695") },
  { k: "fu2017",        s: J("N. Fu, G. S. Sauer, A. Saha, A. Loo and S. Lin", "Science", 2017, 357, "575–579") },
  { k: "malviya2023",   s: J("B. K. Malviya, C. Bottecchia, K. Stone, D. Lehnherr, F. Lévesque, C. O. Kappe and D. Cantillo", "Org. Process Res. Dev.", 2023, 27, "2183–2191") },
  { k: "morofuji2013",  s: J("T. Morofuji, A. Shimizu and J.-i. Yoshida", "J. Am. Chem. Soc.", 2013, 135, "5000–5003") },
  { k: "zhangxu2018",   s: J("S. Zhang, L. Li, M. Xue, R. Zhang, K. Xu and C. Zeng", "Org. Lett.", 2018, 20, "3443–3446") },
  { k: "cai2021",       s: J("C.-Y. Cai, Z.-J. Wu, J.-Y. Liu, M. Chen, J. Song and H.-C. Xu", "Nat. Commun.", 2021, 12, "3745") },
  { k: "zhangye2022",   s: J("L. Zhang, Y. Fu, Y. Shen, C. Liu, M. Sun, R. Cheng, W. Zhu, X. Qian, Y. Ma and J. Ye", "Nat. Commun.", 2022, 13, "4138") },
  { k: "gnaim2022",     s: J("S. Gnaim et al.", "Nature", 2022, 605, "687–695") },
  { k: "hioki2023",     s: J("Y. Hioki, M. Costantini, J. Griffin, K. C. Harper, M. Prado Merini, B. Nissl, Y. Kawamata and P. S. Baran", "Science", 2023, 380, "81–87") },
  { k: "zhangbaran2022",s: J("B. Zhang, Y. Gao, Y. Hioki, M. S. Oderinde, J. X. Qiao, K. X. Rodriguez, H.-J. Zhang, Y. Kawamata and P. S. Baran", "Nature", 2022, 606, "313–318") },
  { k: "kirste2012",    s: J("A. Kirste, B. Elsler, G. Schnakenburg and S. R. Waldvogel", "J. Am. Chem. Soc.", 2012, 134, "3571–3576") },
  { k: "liwilden2020",  s: J("D. Li, T.-K. Ma, R. J. Scott and J. D. Wilden", "Chem. Sci.", 2020, 11, "5333–5338") },
  { k: "qiu2018",       s: J("Y. Qiu, W.-J. Kong, J. Struwe, N. Sauermann, T. Rogge, A. Scheremetjew and L. Ackermann", "Angew. Chem., Int. Ed.", 2018, 57, "5828–5832") },
  { k: "cai2022",       s: J("C.-Y. Cai, X.-L. Lai, Y. Wang, H.-H. Hu, J. Song, Y. Yang, C. Wang and H.-C. Xu", "Nat. Catal.", 2022, 5, "943–951") },
  { k: "courtois1997",  s: J("V. Courtois, R. Barhdadi, M. Troupel and J. Périchon", "Tetrahedron", 1997, 53, "11569–11576") },
  { k: "osa1994",       s: J("T. Osa, Y. Kashiwagi, Y. Yanagisawa and J. M. Bobbitt", "J. Chem. Soc., Chem. Commun.", 1994, null, "2535–2537") },
  { k: "kisukuri2024",  s: J("C. M. Kisukuri, J. Seidler, T. Gärtner, D. F. Rohrmann and S. R. Waldvogel", "Org. Process Res. Dev.", 2024, 28, "1474–1485") },
  { k: "kawamata2021",  s: J("Y. Kawamata, K. Hayashi, E. Carlson, S. Shaji, D. Waldmann, B. J. Simmons, J. T. Edwards, C. W. Zapf, M. Saito and P. S. Baran", "J. Am. Chem. Soc.", 2021, 143, "16580–16588") },
  { k: "ke2019",        s: J("J. Ke, H. Wang, L. Zhou, C. Mou, J. Zhang, L. Pan and Y. R. Chi", "Chem. – Eur. J.", 2019, 25, "6911–6914") },
  { k: "lopezruiz2018", s: J("J. A. Lopez-Ruiz, U. Sanyal, J. Egbert, O. Y. Gutiérrez and J. Holladay", "ACS Sustainable Chem. Eng.", 2018, 6, "16073–16085") },
  { k: "zhong2021",     s: J("X. Zhong, M. A. Hoque, M. D. Graaf, K. C. Harper, F. Wang, J. D. Genders and S. S. Stahl", "Org. Process Res. Dev.", 2021, 25, "2601–2607") },
  { k: "horn2016",      s: J("E. J. Horn, B. R. Rosen, Y. Chen, J. Tang, K. Chen, M. D. Eastgate and P. S. Baran", "Nature", 2016, 533, "77–81") },
  { k: "cardiel2019",   s: J("A. C. Cardiel, B. J. Taitt and K.-S. Choi", "ACS Sustainable Chem. Eng.", 2019, 7, "11138–11149") },
  { k: "okada2016",     s: J("Y. Okada, Y. Yamaguchi, A. Ozaki and K. Chiba", "Chem. Sci.", 2016, 7, "6387–6393") },
  { k: "miller1992",    s: J("D. G. Miller and D. D. M. Wayner", "Can. J. Chem.", 1992, 70, "2485–2490") },
  { k: "walecka2022",   s: J("A. Walęcka-Kurczyk, J. Adamek, K. Walczak, M. Michalak and A. Październiok-Holewa", "RSC Adv.", 2022, 12, "2107–2114") },
  { k: "bao2022",       s: J("L. Bao, C. Liu, W. Li, J. Yu, M. Wang and Y. Zhang", "Org. Lett.", 2022, 24, "5762–5766") },
  { k: "ozaki1994",     s: J("S. Ozaki, I. Horiguchi, H. Matsushita and H. Ohmori", "Tetrahedron Lett.", 1994, 35, "725–728") },
  { k: "zhangzeng2018", s: J("S. Zhang, L. Li, H. Wang, Q. Li, W. Liu, K. Xu and C. Zeng", "Org. Lett.", 2018, 20, "252–255") },
  { k: "tajima2002",    s: J("T. Tajima, H. Ishii and T. Fuchigami", "Electrochem. Commun.", 2002, 4, "589–592") },
  { k: "zhangqiu2025",  s: J("B. Zhang et al.", "Nat. Commun.", 2025, 16, "3052") },
  { k: "gitkis2010",    s: J("A. Gitkis and J. Y. Becker", "Electrochim. Acta", 2010, 55, "5854–5859") },
  { k: "long2021",      s: J("H. Long, C. Huang, Y.-T. Zheng, Z.-Y. Li, L.-H. Jie, J. Song, S. Zhu and H.-C. Xu", "Nat. Commun.", 2021, 12, "6629") },
  { k: "gieshoff2016",  s: J("T. Gieshoff, D. Schollmeyer and S. R. Waldvogel", "Angew. Chem., Int. Ed.", 2016, 55, "9437–9440") },
  { k: "newman",        s: [{ t: "J. Newman and K. E. Thomas-Alyea, " }, { t: "Electrochemical Systems", i: true }, { t: ", John Wiley & Sons, Hoboken, NJ, 3rd edn, 2004." }] },
  { k: "saveant",       s: [{ t: "J.-M. Savéant, " }, { t: "Elements of Molecular and Biomolecular Electrochemistry: An Electrochemical Approach to Electron Transfer Chemistry", i: true }, { t: ", John Wiley & Sons, Hoboken, NJ, 2006." }] },
  { k: "heeb2014",      s: J("M. B. Heeb, J. Criquet, S. G. Zimmermann-Steffens and U. von Gunten", "Water Res.", 2014, 48, "15–42") },
  { k: "wallis1946",    s: J("E. S. Wallis and J. F. Lane", "Org. React.", 1946, 3, "267–306") },
  { k: "denooy1996",    s: J("A. E. J. de Nooy, A. C. Besemer and H. van Bekkum", "Synthesis", 1996, null, "1153–1176") },
  { k: "bailey2007",    s: J("W. F. Bailey, J. M. Bobbitt and K. B. Wiberg", "J. Org. Chem.", 2007, 72, "4504–4509") },
  { k: "badalyan2016",  s: J("A. Badalyan and S. S. Stahl", "Nature", 2016, 535, "406–410") },
  { k: "livongunten2020", s: J("J. Li, J. Jiang, T. Manasfi and U. von Gunten", "Water Res.", 2020, 187, "116424") },
  { k: "lau2019",       s: J("S. S. Lau, K. P. Reber and A. L. Roberts", "Environ. Sci. Technol.", 2019, 53, "11133–11141") },
  { k: "koshino2003",   s: J("N. Koshino, B. Saha and J. H. Espenson", "J. Org. Chem.", 2003, 68, "9364–9370") },
  { k: "nutting2018",   s: J("J. E. Nutting, M. Rafiee and S. S. Stahl", "Chem. Rev.", 2018, 118, "4834–4885") },
  { k: "yang2023",      s: J("C. Yang, S. Arora, S. Maldonado, D. A. Pratt and C. R. J. Stephenson", "Nat. Rev. Chem.", 2023, 7, "653–666") },
  { k: "vo2024",        s: J("N. T. Vo, Q. Cacciuttolo, D. Pasquier and K. Larmier", "ChemElectroChem", 2024, 11, "e202400116") },
  { k: "grennberg1993", s: J("H. Grennberg, A. Gogoll and J.-E. Bäckvall", "Organometallics", 1993, 12, "1790–1793") },
  { k: "hull2009",      s: J("K. L. Hull and M. S. Sanford", "J. Am. Chem. Soc.", 2009, 131, "9651–9653") },
  { k: "sivey2015",     s: J("J. D. Sivey, M. A. Bickley and D. A. Victor", "Environ. Sci. Technol.", 2015, 49, "4937–4945") },
  { k: "ruasse1993",    s: J("M.-F. Ruasse", "Adv. Phys. Org. Chem.", 1993, 28, "207–291") },
  { k: "nagy2007",      s: J("P. Nagy, K. Lemma and M. T. Ashby", "Inorg. Chem.", 2007, 46, "285–292") },
  { k: "ting2022",      s: J("S. I. Ting, W. L. Williams and A. G. Doyle", "J. Am. Chem. Soc.", 2022, 144, "5575–5582") },
  { k: "till2021",      s: J("N. A. Till, S. Oh, D. W. C. MacMillan and M. J. Bird", "J. Am. Chem. Soc.", 2021, 143, "9332–9337") },
  { k: "boucher2023",   s: J("D. G. Boucher, A. D. Pendergast, X. Wu, Z. A. Nguyen, R. G. Jadhav, S. Lin, H. S. White and S. D. Minteer", "J. Am. Chem. Soc.", 2023, 145, "17665–17677") },
  { k: "wilson2024",    s: J("C. V. Wilson and P. L. Holland", "J. Am. Chem. Soc.", 2024, 146, "2685–2700") },
  { k: "lobaccaro2016", s: J("P. Lobaccaro, M. R. Singh, E. L. Clark, Y. Kwon, A. T. Bell and J. W. Ager", "Phys. Chem. Chem. Phys.", 2016, 18, "26777–26785") },

  { k: "gorski2025",    s: J("B. Górski et al.", "Nature", 2025, 637, "354–361") },
];
const RN = {};
if (process.env.SI_REFORDER) JSON.parse(fs.readFileSync(process.env.SI_REFORDER, "utf8")).forEach((k, i) => { RN[k] = i + 1; });
else REFS.forEach((r, i) => { RN[r.k] = i + 1; });
const REFKNOWN = new Set(REFS.map(r => r.k));
const SEEN = [];
// In the condensed second pass a detailed-only element still resolves its markers while it is built; it gets "?" and is never placed.
const refNum = (k) => { if (!REFKNOWN.has(k)) throw new Error("Unknown reference key: " + k); SEEN.push(k); return k in RN ? String(RN[k]) : "?"; };
// In-text markers: «key» or «k1,k2» -> superscript number(s); ⟦key⟧ or ⟦k1,k2⟧ -> plain number(s) (for table cells).
function runsFromText(text, size, base = {}) {
  // **bold** is honoured rather than printed. Ten literal ** markers were shipping in the SI --
  // markdown emphasis that nothing rendered, so a reader saw the asterisks. Split on the pairs
  // first, then run the citation scanner over each piece so a citation inside a bold span still
  // resolves. An unpaired ** is left alone rather than silently eating the rest of a paragraph.
  if (text.includes("**")) {
    const parts = text.split("**");
    if (parts.length % 2 === 1) {                       // balanced: odd indices are the bold ones
      const out = [];
      parts.forEach((piece, k) => {
        if (piece === "") return;
        out.push(...runsFromText(piece, size, { ...base, bold: k % 2 === 1 || !!base.bold }));
      });
      return out;
    }
  }
  const runs = []; const re = /«([^»]+)»|⟦([^⟧]+)⟧/g; let last = 0, m;
  const plain = (t) => { for (const piece of subSplit(t)) runs.push(new TextRun({ text: piece.t, size, font: "Calibri", ...base, subScript: piece.sub || undefined })); };
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) plain(text.slice(last, m.index));
    const nums = (m[1] || m[2]).split(",").map(s => refNum(s.trim())).join(",");
    runs.push(new TextRun({ text: nums, size, font: "Calibri", ...base, superScript: !!m[1] }));
    last = re.lastIndex;
  }
  if (last < text.length) plain(text.slice(last));
  return runs;
}
// ---- subscripts (2026-09-11, author: "stuff like i_lim or k_c ... needs to look professional"): prose written as BASE_TOKEN is
// rendered with TOKEN as a subscript run when TOKEN is the longest entry of data/subscript_tokens.json that starts the
// alphanumeric run after the underscore and either exhausts it or is followed by another symbol's underscore (nFD_SC_S).
// data/docx_text.py reads a subscript run back as "_" + text, so every gate phrase keeps its underscore spelling; the Python
// twin is data/subscripts.py. Anything else (H_EXT, si_001) stays a literal underscore and is listed at the end of the build.
const SUBTOK = JSON.parse(fs.readFileSync(path.join(__dirname, "data", "subscript_tokens.json"), "utf8")).tokens.slice().sort((a, b) => b.length - a.length);
const SUB_RE = /(?<=[A-Za-z0-9)\u0370-\u03FF\u00B5])_([A-Za-z0-9]+)/g;
const SUB_STATS = { converted: 0, literal: new Map() };
function subSplit(text) {
  const out = []; let pos = 0; let m; SUB_RE.lastIndex = 0;
  while ((m = SUB_RE.exec(text)) !== null) {
    const run = m[1]; const after = text[m.index + 1 + run.length];
    const tok = SUBTOK.find(t => run.startsWith(t) && (run.length === t.length || after === "_"));
    if (!tok) { SUB_STATS.literal.set(m[0], (SUB_STATS.literal.get(m[0]) || 0) + 1); continue; }
    if (m.index > pos) out.push({ t: text.slice(pos, m.index), sub: false });
    out.push({ t: tok, sub: true }); SUB_STATS.converted += 1;
    pos = m.index + 1 + tok.length; SUB_RE.lastIndex = pos;
  }
  if (pos < text.length) out.push({ t: text.slice(pos), sub: false });
  return out;
}
function auditRefOrder() {
  const firstSeen = []; const seenSet = new Set();
  for (const k of SEEN) if (!seenSet.has(k)) { seenSet.add(k); firstSeen.push(k); }
  const unused = REFS.map(r => r.k).filter(k => !seenSet.has(k));
  if (unused.length) throw new Error("References never cited: " + unused.join(", "));
  const expected = REFS.map(r => r.k);
  for (let i = 0; i < firstSeen.length; i++)
    if (firstSeen[i] !== expected[i])
      throw new Error("Citation-order mismatch at #" + (i + 1) + ": document first-appearance '" + firstSeen[i] +
        "' but REFS order says '" + expected[i] + "'.\nActual first-appearance order:\n" + firstSeen.join(", "));
  console.log("citation audit: " + REFS.length + " references, " + SEEN.length + " citation sites, first-appearance order OK");
  console.log("subscripts: " + SUB_STATS.converted + " rendered; left literal: " + (SUB_STATS.literal.size ? Array.from(SUB_STATS.literal.entries()).map(function (e) { return e[0] + "(" + e[1] + ")"; }).join(", ") : "none"));
}

// ---------- helpers ----------
const tagEl = (el, kind, t, lvl) => { el.__kind = kind; el.__t = String(t); if (lvl) el.__lvl = lvl; return el; };
const p = (text, opts = {}) => tagEl(new Paragraph({
  children: runsFromText(text, 20, { italics: opts.i || false, bold: opts.b || false }),
  spacing: { after: 120 }, alignment: AlignmentType.JUSTIFIED, ...opts.par }), "p", text);
// ---------- native OMML equation helpers (journal-style: centered, number flush right) ----------
const mr   = (t) => new MathRun(t);
const msub = (b, sc) => new MathSubScript({ children: [typeof b === "string" ? mr(b) : b], subScript: [mr(sc)] });
const msup = (b, sc) => new MathSuperScript({ children: [typeof b === "string" ? mr(b) : b], superScript: [mr(sc)] });
const mfr  = (n, d) => new MathFraction({ numerator: n, denominator: d });
const msq  = (c) => new MathRadical({ children: c });
const mrb  = (c) => new MathRoundBrackets({ children: c });
const msb  = (c) => new MathSquareBrackets({ children: c });
const msum = (c, sc) => new MathSum({ children: c, subScript: [mr(sc)] });
const mfun = (nm, arg) => new MathFunction({ name: [mr(nm)], children: [arg] });
const EQW = 9720;
const eqn = (segs, tag, unit) => {
  const kids = [new TextRun({ text: "\t" })];
  for (const s of segs) kids.push(s.m ? new OMath({ children: s.m })
    : new TextRun({ text: s.t, size: 19, font: "Calibri", italics: true }));
  if (unit) kids.push(new TextRun({ text: "   " + unit, size: 18, font: "Calibri" }));
  kids.push(new TextRun({ text: "\t(" + tag + ")", size: 20, font: "Calibri" }));
  return tagEl(new Paragraph({
    tabStops: [{ type: TabStopType.CENTER, position: Math.round(EQW / 2) }, { type: TabStopType.RIGHT, position: EQW }],
    spacing: { before: 100, after: 160 }, children: kids }), "eq", "(" + tag + ")");
};
const h1 = (t) => tagEl(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: t, size: 26, bold: true })], spacing: { before: 280, after: 140 } }), "h", t, 1);
const h2 = (t) => tagEl(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: t, size: 22, bold: true })], spacing: { before: 200, after: 100 } }), "h", t, 2);
const cap = (t) => tagEl(new Paragraph({ children: runsFromText(t, 18, { italics: true }), spacing: { before: 80, after: 160 } }), "cap", t);

function mkTable(headers, rows, colw, budget = 9720) {
  // Rescale the column-width ratios to EXACTLY fill the section's printable width,
  // and force fixed layout so no table can overflow the page.
  const raw = colw.reduce((a, b) => a + b, 0);
  const w = colw.map(x => Math.floor(x * budget / raw));
  w[w.length - 1] += budget - w.reduce((a, b) => a + b, 0);
  const cell = (t, bold, wd, shade) => new TableCell({
    width: { size: wd, type: WidthType.DXA },
    shading: shade ? { type: ShadingType.CLEAR, fill: "DCE6F1" } : undefined,
    margins: { top: 40, bottom: 40, left: 60, right: 60 },
    children: [new Paragraph({ children: runsFromText(String(t), 15, { bold: !!bold }) })] });
  return Object.assign(tagEl(new Table({
    width: { size: budget, type: WidthType.DXA }, columnWidths: w, layout: TableLayoutType.FIXED,
    rows: [new TableRow({ children: headers.map((h, i) => cell(h, true, w[i], true)), tableHeader: true }),
           ...rows.map(r => new TableRow({ children: r.map((v, i) => cell(v, false, w[i])) }))] }),
    "table", headers.join(" | ")), { __cells: rows.map(r => r.map(String).join(" | ")).join("\n") });
}

// ---------- load the 50-reaction table ----------
const csv = fs.readFileSync(RX_CSV, "utf8").trim().split("\n");
function splitCSV(line) {
  const out = []; let cur = "", q = false;
  for (const ch of line) {
    if (ch === '"') q = !q;
    else if (ch === "," && !q) { out.push(cur); cur = ""; }
    else cur += ch;
  }
  out.push(cur); return out;
}
const hdr = splitCSV(csv[0]);
const col = (name) => hdr.indexOf(name);
// The carrier CHARGE is the switch on the migration term and was not printed anywhere in this
// document until 2026-09-05, though it moves ceilings by up to 2x (the anodic decarboxylative
// ruling moved one row 65 %). It comes from data/carrier_charge.csv, the file the NP solver reads
// (run_all50_np.jl), joined by reaction name; G-NAMES asserts the two tables key on the same 50.
const CC_LINES = fs.readFileSync(path.join(DATA, "carrier_charge.csv"), "utf8").trim().split("\n").filter(l => !l.startsWith("#"));
const cchdr = splitCSV(CC_LINES[0]);
const CC = new Map(CC_LINES.slice(1).map(splitCSV).map(r => [r[cchdr.indexOf("reaction")], {
  z: r[cchdr.indexOf("z_carrier")], confidence: r[cchdr.indexOf("confidence")],
  species: r[cchdr.indexOf("carrier_species")], basis: r[cchdr.indexOf("basis")] }]));
const zOf = (rxn) => { const c = CC.get(rxn); if (!c) throw new Error("Table S2: no carrier charge for " + rxn); return c.z + (c.confidence === "high" ? "" : "*"); };
const CC_MEDIUM = [...CC.entries()].filter(([, c]) => c.confidence !== "high").map(([k]) => k);
// The reaction table records how each concentration was checked with an internal label; the printed cell states it in words.
const concProv = (t) => t.replace(/^Declared rather than exemplar-verified\./, "Declared rather than read from the exemplar.")
  .replace(/^Exemplar-verified against /, "Checked against ").replace(/^Exemplar-verified/, "Read from the exemplar");
const rxRows = csv.slice(1).map(splitCSV).map((r, k) => [
  k + 1, r[col("cls")], r[col("reaction")], r[col("carrier_type")], r[col("carrier_species")], zOf(r[col("reaction")]),
  Number(r[col("D_cm2s")]).toExponential(2), r[col("C_carrier_M")], r[col("n_carrier")],
  r[col("solvent")], r[col("electrolyte")], r[col("D_provenance")], concProv(r[col("conc_provenance")])]);

// ---------- load the provenance registry ----------
// Loaded HERE, before any prose, because several sentences in §S4, §S8 and §S9 quote counts out of
// it. Those counts used to be typed into the prose by hand, and every upstream reclassification
// silently falsified them: the 2026-08 kappa pass moved nine conductivities from assumption to
// derived and instantly made the §S8 census (64/79/125) wrong without touching a line of this file.
// Nothing below hardcodes a census any more — census() reads the CSV the tables are printed from,
// so the prose and Table S7 cannot disagree by construction.
// Tables S3 and S4 used to carry hand-typed numbers. That is the drift this project exists to
// prevent, and it had already happened: after HFIP's viscosity was page-anchored to Krumgalz
// Table 3 p. 578 the registry read 1.619 mPa s while Table S3 still printed the unsourced 1.650,
// so the SI contradicted its own appendix. Worse, `1 M NaOH aq` -- one of the four conductivities
// carrying a §S6 verdict -- was shown in Table S4 with a provenance state that came from a
// typed literal rather than from the registry, because it had no registry row at all.
// Both tables now take every numeric and state column from the CSVs at build time. Only the
// prose columns (Source, Margin, Note) remain authored, and they assert nothing numeric.
const SOLV_CSV = fs.readFileSync(path.join(__dirname, "data", "solvents.csv"), "utf8")
  .replace(/\r/g, "").trim().split("\n").slice(1).map(splitCSV);
const SOLV = new Map(SOLV_CSV.map(r => [r[0], { M: r[1], mu: r[2], rho: r[3], phi: r[4] }]));
const ELEC_CSV = fs.readFileSync(path.join(__dirname, "data", "electrolytes.csv"), "utf8")
  .replace(/\r/g, "").trim().split("\n").slice(1).map(splitCSV);
const ELEC = new Map(ELEC_CSV.map(r => [r[0], { kappa: r[1], state: r[2], status: r[3] }]));
// SI display names carry a volume ratio the CSV key does not ("MeCN/H2O 9:1 v/v" -> "MeCN/H2O").
function solvRow(name) {
  if (SOLV.has(name)) return SOLV.get(name);
  const base = name.split(" ")[0];
  if (SOLV.has(base)) return SOLV.get(base);
  throw new Error("Table S3 names a solvent absent from solvents.csv: " + name);
}
function elecRow(name) {
  const norm = name.replace(/ \/ /g, "/").replace(/ \(aq\)/, " aq");
  if (ELEC.has(norm)) return ELEC.get(norm);
  throw new Error("Table S4 names an electrolyte absent from electrolytes.csv: " + name);
}
// Rewrite the numeric columns of a typed row from the CSV, reporting anything that had drifted.
const TABLE_DRIFT = [];
function fromCSV(row, cols, lookup, label) {
  const src = lookup(row[0]);
  const out = row.slice();
  cols.forEach(([i, k]) => {
    const v = String(src[k]);
    const typed = String(out[i]).trim();
    // The CSV is authoritative for the VALUE; the typed string keeps the display precision, but
    // only while the two agree numerically. "0.890" against a registry 0.89 is the same number
    // shown to one more place and must not be reported as drift; 1.650 against 1.619 is drift.
    const same = !isNaN(parseFloat(v)) && !isNaN(parseFloat(typed))
                 && Math.abs(parseFloat(v) - parseFloat(typed)) <= 1e-9 * Math.max(1, Math.abs(parseFloat(v)));
    if (same) return;
    if (typed !== v) TABLE_DRIFT.push(label + " " + row[0] + " [" + k + "] typed "
                                      + typed + " -> registry " + v);
    out[i] = v;
  });
  return out;
}
// ---------- load the PUBLISHED matrix (julia/tier0_ec_matrix.csv) ----------
// Table S5 and every median/count the prose quotes are computed from this file, not typed.
// They were typed until 2026-08-25, and had drifted the moment the solver was corrected: the
// table still read 6.0 / 11/50 / 17/50 / 21/50 / 14/50 / 34/50 while the model gave
// 6.1 / 12 / 18 / 20 / 15 / 33. Same defect Tables S3 and S4 had, one table along.
const MAT = fs.readFileSync(path.join(__dirname, "julia", "tier0_ec_matrix.csv"), "utf8")
  .replace(/\r/g, "").trim().split("\n");
const MHDR = splitCSV(MAT[0]);
const MROW = MAT.slice(1).map(splitCSV);
const mcol = (n) => { const i = MHDR.indexOf(n);
  if (i < 0) throw new Error("tier0_ec_matrix.csv has no column " + n); return i; };
function matStats(key, carrier) {
  const ci = carrier ? mcol("carrier") : -1;
  const v = MROW.filter(r => !carrier || r[ci] === carrier)
                .map(r => Number(r[mcol(key)])).filter(x => !isNaN(x)).sort((a, b) => a - b);
  const n = v.length;
  if (!n) throw new Error("no rows for " + key + "/" + carrier);
  return { n, median: n % 2 ? v[(n - 1) / 2] : (v[n / 2 - 1] + v[n / 2]) / 2,
           ge25: v.filter(x => x >= 25).length, ge50: v.filter(x => x >= 50).length };
}
// ---------- the migration-free Fick layer, for the S7 physics comparison ----------
const FICK = fs.readFileSync(path.join(__dirname, "julia", "tier0_matrix.csv"), "utf8")
  .replace(/\r/g, "").trim().split("\n");
const FHDR = splitCSV(FICK[0]);
const FROW = FICK.slice(1).map(splitCSV);
const fcol = (n) => { const i = FHDR.indexOf(n);
  if (i < 0) throw new Error("tier0_matrix.csv has no column " + n); return i; };
const fickCount = (key, thr) => FROW.filter(r => Number(r[fcol(key)]) >= thr).length;

// ---------- solvent-property exposure (results/solvent_property_sensitivity.json) ----------
// The S5.5 sentence quoting this band was typed and had drifted three ways at once: it said
// eleven rows where the model flags 13, "at most two entries of fifty" where the worst movement
// is 3, and a baseline of 11-17-21-31-36-36 that predates two solver corrections. It went
// unnoticed because G-SOLV (figs/analysis_solvent_property_sensitivity.py) is in no runner.
// Emitted from the JSON now, so the prose cannot disagree with the sweep that produced it.
const SP = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "solvent_property_sensitivity.json"), "utf8"));
const NUMW = ["zero","one","two","three","four","five","six","seven","eight","nine","ten",
              "eleven","twelve","thirteen","fourteen","fifteen","sixteen","seventeen"];
const numw = (n) => NUMW[n] || String(n);
const spSpan = () => SP.per_arch_span[0]
  .map((lo, i) => lo === SP.per_arch_span[1][i] ? String(lo)
                  : lo + "\u2013" + SP.per_arch_span[1][i]).join(" / ");

// ---------- the mediated EC' matrix, for Table S6 ----------
// Same rule as Table S5: the numeric columns are computed, never typed. They had drifted badly --
// the chloride/ethylene row printed "392 -> 789" against a model that gives 196 -> 394, a clean
// factor of two left over from an earlier migration convention.
const MEDC = fs.readFileSync(path.join(__dirname, "julia", "mediated_ec_matrix.csv"), "utf8")
  .replace(/\r/g, "").trim().split("\n");
// ---- the S5.2 termination census, COMPUTED from the matrix (it was typed until 2026-09-05, and the
// ethylene-D re-solve moved "0.13% ... 39 of 48" to "0.14% ... 35 of 48" behind a green build;
// G-ECBAND caught it). Same parse as that gate: the c_red/cb value the limiter string records.
const CENSUS = (() => {
  const rows = MEDC.slice(1);                       // MEDC is already split into lines
  const fr = [];
  let ncoll = 0;
  for (const ln of rows) {
    const m = /c_red\/cb ([0-9.eE+-]+)/.exec(ln);
    if (m) fr.push(100 * parseFloat(m[1]));
    else if (/,"?collapse \(c-control\)/.test(ln)) { fr.push(0.1); ncoll += 1; }   // crossed 1e-3 exactly: at the criterion
  }
  if (fr.length !== rows.length) throw new Error("S5.2 census: " + (rows.length - fr.length) + " mediated cell(s) carry neither a plateau value nor a collapse label");
  return { n: String(rows.length), lo: Math.min(...fr).toFixed(2), hi: Math.max(...fr).toFixed(1),
           n028: String(fr.filter(v => v <= 0.28).length), ncoll: String(ncoll) };
})();
const EHDR = splitCSV(MEDC[0]);
const ecol = (n) => { const i = EHDR.indexOf(n);
  if (i < 0) throw new Error("mediated_ec_matrix.csv has no column " + n); return i; };
const EROW = MEDC.slice(1).map(splitCSV);
// ---- the log-log slope of each mediated row against the film, computed here so that the
// manuscript's pointer to this table resolves to content rather than only to a heading.
// Same construction as figs/model_medians.mediated_delta_slopes: least squares of ln(i_EC) on
// ln(delta) over the rows the solver flags ok, which is the model's own convergence flag.
const MED_SLOPES = (() => {
  const by = {};
  EROW.forEach(r => {
    if (r[ecol("flag")] !== "ok") return;
    (by[r[ecol("reaction")]] = by[r[ecol("reaction")]] || [])
      .push([Math.log(Number(r[ecol("delta_um")])), Math.log(Number(r[ecol("i_ec_mAcm2")]))]);
  });
  const out = {};
  for (const k of Object.keys(by)) {
    const v = by[k], n = v.length;
    const mx = v.reduce((a, p) => a + p[0], 0) / n, my = v.reduce((a, p) => a + p[1], 0) / n;
    out[k] = v.reduce((a, p) => a + (p[0] - mx) * (p[1] - my), 0)
           / v.reduce((a, p) => a + (p[0] - mx) * (p[0] - mx), 0);
  }
  return out;
})();
const MED_SLOPE_SENT = (() => {
  const e = Object.keys(MED_SLOPES).map(k => [k, MED_SLOPES[k]]).sort((a, b) => b[1] - a[1]);
  const flat = e.filter(x => x[1] > -0.5), steep = e.filter(x => x[1] <= -0.5);
  const fmt = (x) => "\u2212" + Math.abs(x).toFixed(2);
  const nrx = new Set(EROW.map(r => r[ecol("reactor")])).size;
  return "Fitting ln i_lim against ln \u03b4 across the " + nrx + " archetype films "
    + "separates the rows the film governs from the rows it does not: " + flat.length + " of the "
    + e.length + " are nearly flat (" + flat.map(x => fmt(x[1])).join(" and ") + ", the "
    + "kinetically limited entries), while the remaining " + steep.length + " span " + fmt(steep[0][1])
    + " to " + fmt(steep[steep.length - 1][1]) + ", approaching the pure-Fick value of \u22121 "
    + "wherever transport of substrate or of mediator sets the ceiling.";
})();
function ecCell(rxn, reactor) {
  const r = EROW.find(x => x[ecol("reaction")] === rxn && x[ecol("reactor")] === reactor);
  if (!r) throw new Error("mediated_ec_matrix.csv has no cell " + rxn + " / " + reactor);
  return { xk: Number(r[ecol("xk_um")]), t0: Number(r[ecol("i_tier0_mAcm2")]),
           ec: Number(r[ecol("i_ec_mAcm2")]), limiter: r[ecol("limiter")] };
}
// Display conventions already used by this table: x_k to one decimal below 100, currents to a
// whole number at and above 10.
const fxk  = (v) => v >= 100 ? String(Math.round(v)) : v.toFixed(1);
const fcur = (v) => v >= 10  ? String(Math.round(v)) : v.toFixed(1);
// ---- S5.2 / S5.5 mediated-matrix facts, COMPUTED (they were typed until 2026-09-07 and had been stale
// since the batch films moved: "delta/x_k ~ 43 stirred", "at 128", "104.7", "amplifications x1.0 to x27",
// "2/8 to 3/8 (>=25: 2/8 to 4/8)" all described the 100 um / 300 um films behind green gates)
const EC = EROW.map(r => ({ rxn: r[ecol("reaction")], reactor: r[ecol("reactor")], delta: Number(r[ecol("delta_um")]),
                            xk: Number(r[ecol("xk_um")]), t0: Number(r[ecol("i_tier0_mAcm2")]), ec: Number(r[ecol("i_ec_mAcm2")]),
                            sav: Number(r[ecol("i_saveant_mAcm2")]), cap: Number(r[ecol("i_subcap_mAcm2")]),
                            limiter: r[ecol("limiter")], path: r[ecol("path")] }));
// The S5.5 bracket: every mediated cell replaced by its closed-form envelope min(Saveant, substrate supply)
// and, separately, by its Stage-0 floor; the >=25 count per architecture over the three variants gives the
// band. Same construction as the gate that checks it (it was a typed "10-12, 12-14, ..." until 2026-09-07).
// (a function, not an IIFE: ARCH and ORDERING_TEXT are defined further down; it is called where the sentence is built)
const bracket = () => {
  const label = Object.fromEntries(ARCH.map(([lab, k]) => [k, lab]));
  const medSet = new Set(EC.map(c => c.rxn));
  const out = [];
  for (const [, k] of ARCH) {
    const base = MROW.filter(r => !medSet.has(r[mcol("reaction")])).map(r => Number(r[mcol(k)]));
    // the solver writes the microfluidic label with "um"; the SI prints it with the Greek letter
    const mlabel = k === "micro" ? "Microfluidic cell (25 um gap)" : label[k];
    const cells = EC.filter(c => c.reactor === mlabel);
    if (cells.length !== 8) throw new Error("bracket: " + k + " has " + cells.length + " mediated cells (label " + mlabel + ")");
    const n = (vals) => base.concat(vals).filter(v => v >= 25).length;
    const v = [n(cells.map(c => c.ec)), n(cells.map(c => c.t0)), n(cells.map(c => Math.min(c.sav, c.cap)))];
    out.push(Math.min(...v) + "\u2013" + Math.max(...v));
  }
  const above = EC.filter(c => c.ec > Math.min(c.sav, c.cap)).length, aboveCap = EC.filter(c => c.ec > c.cap).length;
  return { text: out.slice(0, -1).join(", ") + " and " + out[out.length - 1], above, aboveCap, n: EC.length };
};
const ecAmp = (c) => c.ec / c.t0;
const ecRows = (frag) => EC.filter(c => c.rxn.includes(frag));
const ecOne = (frag, reactor) => { const c = EC.find(x => x.rxn.includes(frag) && x.reactor === reactor); if (!c) throw new Error("no EC cell " + frag + " / " + reactor); return c; };
const fRange = (vals, f) => f(Math.min(...vals)) + "\u2013" + f(Math.max(...vals));
const AMP_ALL = "\u00d7" + Math.min(...EC.map(ecAmp)).toFixed(1) + " to \u00d7" + Math.round(Math.max(...EC.map(ecAmp)));
const ecCount = (reactor, thr, key) => EC.filter(c => c.reactor === reactor && c[key] >= thr).length;
const HOF_ST = ecOne("Hofmann", "Stirred batch"), HOF_UN = ecOne("Hofmann", "Unstirred batch");
const ACT = ecRows("ACT-mediated"), HMF = ecRows("HMF"), NHPI = ecRows("NHPI");
const batchOf = (rows) => rows.filter(c => /batch/.test(c.reactor));
const WALL = EC.filter(c => /^newton-wall/i.test(c.limiter));
const WALLNAME = { "Unstirred batch": "unstirred-batch", "Stirred batch": "stirred-batch", "Recirculating flow cell": "recirculating-flow",
                   "ANEC flow cell": "ANEC", "Microfluidic cell (25 um gap)": "microfluidic", "RDE 1600 rpm": "rotating-disk",
                   "Rotating cylinder 3000 rpm": "rotating-cylinder" };
const listAnd = (xs) => xs.length <= 1 ? xs.join("") : xs.slice(0, -1).join(", ") + " and " + xs[xs.length - 1];
if (WALL.length === 0 || new Set(WALL.map(c => c.rxn)).size !== 1 || !WALL[0].rxn.includes("Cl-mediated ethylene"))
  throw new Error("the S5.2 wall sentence assumes the wall cells all belong to the Cl-/ethylene system; matrix has " + JSON.stringify(WALL.map(c => c.rxn + "/" + c.reactor)));
const WALL_SENT = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"][WALL.length] + " cells \u2014 the " + listAnd(WALL.map(c => WALLNAME[c.reactor] || (() => { throw new Error("no wall name for " + c.reactor); })())) + " architectures of the Cl\u207b/ethylene system \u2014";
const DXK_MAX = EC.reduce((a, c) => (c.delta / c.xk > a.delta / a.xk ? c : a), EC[0]);
if (DXK_MAX !== HOF_UN) throw new Error("S5.2 says the Hofmann/unstirred cell has the largest delta/x_k; the matrix says " + DXK_MAX.rxn + " / " + DXK_MAX.reactor);
// SI display label -> the reaction name the solver writes.
const S6MAP = {
  "Br⁻ / Hofmann rearrangement (80 mM, MeCN)": "Br-mediated Hofmann rearrangement",
  "ACT / alcohol oxidation (25 mM, aq. pH 8.5)": "ACT-mediated alcohol oxidation (flow, hectogram)",
  "Cl⁻ / ethylene epoxidation (1 M KCl, aq.)": "Cl-mediated ethylene epoxidation",
  "Cl₄NHPI / allylic C–H (33 mM, acetone)": "NHPI-mediated allylic C-H -> enone",
  "ACT / HMF → FDCA (40 mM, aq. pH 10)": "HMF -> FDCA (biomass)",
  "BQ / Wacker–Tsuji (22 mM, MeCN/H₂O)": "BQ-mediated Wacker-Tsuji oxidation",
  "Br⁻ / electrophilic bromination (0.152 M, aq./MeCN/MeOH/DCM)": "Br- oxidation / electrophilic bromination",
  "SCN⁻ / thiocyanation (0.1 M, AcOH/HCOOH)": "Aryl thiocyanation (NH4SCN)",
};
// Rewrite columns 3-5 (x_k, stirred Stage-0 -> EC', ANEC Stage-0 -> EC') from the matrix, and
// retire a "Newton-wall lower bound" note on any row where neither shown reactor stalls any more.
function s6FromMatrix(rows) {
  return rows.map(row => {
    const rxn = S6MAP[row[0]];
    if (!rxn) throw new Error("Table S6 row has no matrix mapping: " + row[0]);
    const st = ecCell(rxn, "Stirred batch"), tg = ecCell(rxn, "ANEC flow cell");
    const out = row.slice();
    out[3] = fxk(st.xk);
    out[4] = fcur(st.t0) + " → " + fcur(st.ec);
    out[5] = fcur(tg.t0) + " → " + fcur(tg.ec);
    const walled = /newton-wall/i.test(st.limiter) || /newton-wall/i.test(tg.limiter);
    if (!walled && /Newton-wall/i.test(out[6])) out[6] = "mediator plateau (c-control)";
    return out;
  });
}
const ARCH = [["Unstirred batch", "natural"], ["Stirred batch", "stirred"],
              ["Recirculating flow cell", "flow"], ["ANEC flow cell", "anec"],
              ["Microfluidic cell (25 \u03bcm gap)", "micro"],
              ["RDE 1600 rpm", "rde"], ["Rotating cylinder 3000 rpm", "rce"]];
const N_CELLS = 50 * ARCH.length;            // 350: the published matrix, seven archetypes
// THE ORDERING CLAIM (2026-09-07). With seven archetypes the medians of the three thin-film cells
// (microfluidic, RDE, rotating cylinder) lie within ~20 % of one another and are not claimed to be
// ordered; the claim is the four-step chain through the ANEC cell, with every thin-film archetype
// above it. Asserted here so the sentences below cannot outlive the matrix that licenses them.
const ORDER_CHAIN = ["natural", "stirred", "flow", "anec"], ORDER_THIN = ["micro", "rde", "rce"];
const ORDERING_TEXT = "unstirred < stirred < recirculating flow < ANEC, with the microfluidic, RDE and rotating-cylinder medians all above ANEC";
const MS = new Map(ARCH.map(([, k]) => [k, matStats(k)]));
(() => {
  const m = (k) => MS.get(k).median;
  const chainOK = ORDER_CHAIN.every((k, i) => i === 0 || m(ORDER_CHAIN[i - 1]) < m(k));
  const thinOK = ORDER_THIN.every(k => m(k) > m("anec"));
  if (!chainOK || !thinOK) throw new Error("the architecture-ordering claim (" + ORDERING_TEXT + ") does not hold on the matrix: " +
      ARCH.map(([, k]) => k + " " + m(k).toFixed(2)).join(", "));
})();
// >=100 mA cm-2 is quoted as a whole number, below that to one decimal -- the convention the
// manuscript already uses ("6, 17, 19, 49, 108 and 122").
const med  = (k) => { const m = MS.get(k).median; return m >= 100 ? String(Math.round(m)) : m.toFixed(1); };
const medI = (k) => String(Math.round(MS.get(k).median));
const ge25 = (k) => MS.get(k).ge25 + "/" + MS.get(k).n;
const ge50 = (k) => MS.get(k).ge50 + "/" + MS.get(k).n;

const pcsv = fs.readFileSync(PROV_CSV, "utf8").replace(/\r/g, "").trim().split("\n");
const phdr = splitCSV(pcsv[0]);
const pcol = (n) => phdr.indexOf(n);
let prows = pcsv.slice(1).map(splitCSV);
// ---- PUBLISHED SUBSET -------------------------------------------------------------------
// The SI prints the parameters a reader needs in order to check a claim, not the ones that exist
// only because the model was built incrementally. data/registry_liveness.py applies a stated rule
// (a row is dead if its solvent is used by no reaction, or its own registry text declares it
// display-only) and writes the two lists. Filtering here rather than in the registry keeps
// parameters_provenance.csv complete as the internal record and as the provenance file for the
// code, while the published appendix carries only load-bearing rows.
//
// This is a disclosed omission, not a silent one: the count and the reason are stated in §S9.
const LIVENESS = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "registry_liveness.json"), "utf8"));
const DEAD = new Set(LIVENESS.dead_parameters);
const N_OMITTED = LIVENESS.n_dead;
if (LIVENESS.n_total !== prows.length) {
  throw new Error("registry_liveness.json describes " + LIVENESS.n_total + " rows but the "
                  + "registry has " + prows.length + "; re-run data/registry_liveness.py");
}
const ALLROWS = prows;                       // the complete internal record, before the trim
prows = prows.filter(r => !DEAD.has(r[pcol("parameter")]));
// Table S7's blocks are lettered (a), (b), ... in THIS order, and the SI cites them by letter
// ("Table S7g" for the stirred-batch delta band, "Table S7i" for sigma and the design currents).
// Taken in CSV first-appearance order the categories run 1,2,3,4,5,6,9,7,8,10,11 -- category 9
// sits between 6 and 7 -- so every letter after (f) shifted and two citations pointed at the
// wrong block: delta lives in "7. Reactors" which was lettered (h), while (g) was "9. Thermal
// model". Sorting by the leading category number restores the order the prose was written
// against, and makes S7c/S7d/S7f/S7g/S7i all correct. G-GHOST asserts the mapping.
const pcats = [...new Set(prows.map(r => r[pcol("category")]))]
  .sort((x, y) => (parseInt(x, 10) || 0) - (parseInt(y, 10) || 0));
function census(filter) {
  const rs = filter ? prows.filter(filter) : prows;
  const c = { n: rs.length, measured: 0, derived: 0, assumption: 0 };
  rs.forEach(r => { c[r[pcol("provenance_class")]]++; });
  return c;
}
const CAT = (frag) => (r) => r[pcol("category")].includes(frag);
// Number agreement for the templated censuses. Without it the counts, which are computed, land
// inside prose that was written when they were larger: "1 are derived and 1 are assumptions",
// "seven of those 1". A census that is right and reads as broken is not better than a wrong one.
const isAre = (n) => (n === 1 ? "is" : "are");
const nOf = (n, sing, plur) => n + " " + (n === 1 ? sing : (plur || sing + "s"));
const CENSUS_ALL  = census();
const CENSUS_COND = census(CAT("Electrolyte conductivities"));
const CENSUS_DIFF = census(CAT("Solver species diffusivities"));
// Census over EVERY row, trimmed or not. The sentence in S9 that contrasts the two sets used to
// TYPE this one ("0 measured, 8 derived and 41 assumption") while computing the other, so when
// three conductivities became measured the contrast sentence kept asserting a data gap the
// tables on the facing page had already partly closed. Nothing about a census may be typed.
function censusAll(filter) {
  const rs = filter ? ALLROWS.filter(filter) : ALLROWS;
  const c = { n: rs.length, measured: 0, derived: 0, assumption: 0 };
  rs.forEach(r => { c[r[pcol("provenance_class")]]++; });
  return c;
}
const CENSUS_COND_ALL = censusAll(CAT("Electrolyte conductivities"));
// The four conductivities that carry a §S6 conclusion; the rest of category 6 is display-only
// because kappa enters no transport quantity (see the Table S4 caption).
const N_COND_CONCLUSION = 4;
// The assumption LEDGER (figs/analysis_assumption_ledger.py -> results/assumption_ledger.json).
// A bare "N assumption" invites the reading that N numbers were invented. The ledger sorts every
// state-C row by what actually backs it, and these counts are read from its output rather than
// typed, so the prose cannot drift from the classifier. If the file is absent the sentence is
// omitted entirely rather than falling back to a stale literal.
// ---- SI sensitivity bounds (results/si_sensitivity_bounds.json) --------------------------------
// Generated by data/si_sensitivity_bounds.py and gated by data/check_si_bounds.py (G-SIBOUNDS),
// which asserts that every value lies inside its own bounds AND that every number G-MSDERIVED
// checks against the manuscript is either bounded here or exempt with a stated reason. Loaded
// rather than typed so the section cannot drift from the model it describes.
const BOUNDS = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "si_sensitivity_bounds.json"), "utf8"));

// ---- kappa(T) bracket (results/figK_kappaT_sensitivity.json) ----------------------------------
// The MeCN/microfluidic reversal used to be TYPED into S6.3 as "440 ... and 563". The boiling
// points moved to their CRC values on 2026-08-30 and those two literals did not, so S6.3 printed
// 440 while S6.1, three paragraphs earlier, printed the corrected 438 FOR THE SAME QUANTITY --
// the document disagreed with itself. Both ends are computed here now (trap 10: never type an
// expectation you could derive), and figs/analysis_kappaT_sensitivity.py (G-KAPPAT) parses the
// finished sentence back out of the .docx and re-checks it against the model.
// ---- reactor-engineering quantities (results/reactor_engineering.json) -----------------------
// A limiting current density is a FLUX. S8.1 reports the productivity quantities it cannot
// express, computed from the SAME channel geometry the Leveque correlation uses.
const RE = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "reactor_engineering.json"), "utf8"));
const reA = RE.channels[0], reB = RE.channels[1], reR = RE.ratios;

// ---- what the dataset can say about operating current density (Jonas Rein's "(<XX mA cm-2)")
// results/dataset_current_density.json, from data/dataset_current_density.py
const DJ = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "dataset_current_density.json"), "utf8"));
if (DJ.verdict !== "PASS") throw new Error("dataset_current_density.json is not PASS");

// ---- dilute-theory stratification (results/dilute_theory_stratify.json) ----------------------
// S1.1 (i) already declares that above ~1 M the constant-mobility assumption is quantitatively
// wrong. The reviewer's NEXT question is the one a declaration does not answer: how much of the
// headline count comes from exactly those rows? Computed, never typed.
const DS = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "dilute_theory_stratify.json"), "utf8"));

// ---- EC' panel-boundary exposure (results/ecprime_panel_sensitivity.json) --------------------
// The two diffusivities of the S5.4 / §S5.4 base case are state-C declarations, and main-text Fig. 6d-f draws three real
// rows whose regime labels come from the solve; the gate states how far the boundaries move and whether the labels survive.
const EP = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "ecprime_panel_sensitivity.json"), "utf8"));

// ---- internal-film series bound (results/hint_series_bound.json) -----------------------------
const HB = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "hint_series_bound.json"), "utf8"));

// ---- Schmidt-range extrapolation of the RCE correlation (results/schmidt_extrapolation.json) --
const SX = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "schmidt_extrapolation.json"), "utf8"));

// ---- ex-cell illustrative solve (results/excell.json, written by julia/run_excell.jl) ---------
// Every number in the ex-cell passage of S4 is interpolated from the solver's own JSON, inputs
// included, so the passage cannot drift from the solve (it did: the solver carried a C_sat the
// registry had withdrawn, and the passage printed the numbers that value produced).
const EX = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "excell.json"), "utf8"));
// ---- unstirred-batch film derivation (results/free_convection_delta.json) --------------------
const FC = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "free_convection_delta.json"), "utf8"));
// ---- supporting-ion class defaults and what they cost (results/unsourced_D_sensitivity.json) -----
const UD = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "unsourced_D_sensitivity.json"), "utf8"));
// ---- carrier-charge sweep (results/carrier_charge_sensitivity.json, G-ZSENS) --------------------
const ZS = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "carrier_charge_sensitivity.json"), "utf8"));
// ---- the eleven catalyst rows under a finite k (results/catalyst_ec_sensitivity.json, G-CATK) ----
// The published matrix runs every molecular-catalyst row at k = 0: turned over at the electrode,
// credited with no regeneration inside the film, ceiling = the carrier's own transport bound. That
// is the FLOOR of the EC' current, so every sentence that says what the class can and cannot do is
// a k = 0 statement and must say so. G-CATK re-solves the eleven rows as EC' problems over a
// declared k band; nothing below is typed -- every number is read from its artifact.
const CK = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "catalyst_ec_sensitivity.json"), "utf8"));
// 2026-09-11: the Stokes-Einstein radius exposure (results/catalyst_D_sensitivity.json, G-CATD): with the deciding
// catalyst row at its sourced rate constant the ten-of-eleven count is CONDITIONAL on the assigned radius, and the
// S3 passage states the break radius the gate computes rather than a typed margin.
const CD = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "catalyst_D_sensitivity.json"), "utf8"));
const cdShort = (nm) => nm.replace(/ \(.*$/, "");
const cdSentence = () => CD.conditional
  ? ("At the assigned radii ten of eleven catalyst-carried entries clear 25 mA cm⁻² in no architecture, but the count is conditional on this "
     + "input at the sourced rate constants of §S5.7: it breaks at r_h = " + CD.r_crit_from_4p5A.toFixed(2) + " Å on the deciding row (" + cdShort(CD.deciding_row)
     + ", " + CD.second_best_i_lim.toFixed(1) + " mA cm⁻² at best, " + CD.f_crit.toFixed(2) + "× short of the threshold), inside the assigned 4–5 Å band and above "
     + "the " + CD.r_expected_deciding_A.toFixed(2) + " Å that size-scaling the ferrocene anchor predicts for that complex. The 1/r_h scaling behind that figure is "
     + "the k = 0 law and a bound for the sourced rows, whose ceiling goes as √D in the kinetic regime, which moves the break to " + CD.r_crit_sqrt_from_4p5A.toFixed(2) + " Å.")
  : ("The conclusion that rests on it — that ten of eleven catalyst-carried entries clear 25 mA cm⁻² in no architecture — breaks only at r_h = "
     + CD.r_crit_from_4p5A.toFixed(2) + " Å, below the " + CD.r_expected_deciding_A.toFixed(2) + " Å that size-scaling the ferrocene anchor predicts for the deciding row.");
const ckK = CK.k_band_M.map(Number); const ckKmax = Math.max(...ckK);
const ckAt = (k) => CK.per_k[String(k)];
const ckSurv = (k) => CK.ten_of_eleven_survives_at_k[String(k)];
const ckKhold = (() => { let h = null; for (const k of ckK) { if (ckSurv(k)) h = k; else break; } return h; })();
const ckKfail = (() => { for (const k of ckK) if (!ckSurv(k)) return k; return null; })();
const ckN25 = (k) => ckAt(k).clear25;
const ckAmp = ckAt(ckKmax).max_amplification;
const ckRows = Object.entries(CK.per_row);
const ckCapped = ckRows.filter(([, r]) => r.substrate_capped_at_kmax).length;
const ckClearCapped = ckRows.filter(([, r]) => r.k_min_clearing25 && r.k_min_clearing25.at_substrate_cap).length;
const ckSci = (k) => k >= 1000 ? "10" + { 1000: "³", 10000: "⁴", 100000: "⁵" }[k] : String(k);
const ckShort = (nm) => nm.replace(/ \(.*$/, "");
const ckCsRange = (() => { const c = ckRows.map(([, r]) => r.C_S_M).filter(x => x != null); return c.length ? [Math.min(...c), Math.max(...c)] : null; })();
// 2026-09-11: seven of the eleven rows are carried at a SOURCED rate constant (the G-CATK sourced block;
// docs/CATALYST_RATE_CONSTANTS_20260911.md). Every number below is read from that block.
const SR = CK.sourced || null;
const srK = (k) => ({ 1: "1", 10: "10", 100: "10²", 700: "7 × 10²", 1000: "10³", 10000: "10⁴" })[k] || String(k);
const srRow = (nm) => (SR ? SR.per_row[nm] : null);
const srBy = (pfx) => (SR ? Object.entries(SR.per_row).filter(([, r]) => r.basis.startsWith(pfx)) : []);
const srCountMoves = () => {
  if (!SR) return "";
  const names = { natural: "unstirred", stirred: "stirred", flow: "recirculating-flow", anec: "ANEC", micro: "microfluidic", rde: "RDE", rce: "rotating-cylinder" };
  const mv = [];
  for (const [a, d] of Object.entries(SR.count_delta_at_band_edges))
    for (const [t, x] of Object.entries(d)) if (x[0] !== 0 || x[1] !== 0) mv.push(names[a] + " ≥" + t + " count " + (x[0] > 0 ? "+" : "") + x[0] + " at the low edge and " + (x[1] > 0 ? "+" : "") + x[1] + " at the high edge");
  return mv.length ? "With every sourced row moved to the edges of its measured bracket at once, the fifty-row counts move by at most " + SR.max_abs_count_delta + " entr" + (SR.max_abs_count_delta === 1 ? "y" : "ies") + " (" + mv.join("; ") + "); no other count moves." : "With every sourced row moved to the edges of its measured bracket at once, no ≥25 or ≥50 count moves.";
};
const ckClearList = () => ckAt(ckKmax).rows_clearing25.map(nm => {
  const r = CK.per_row[nm]; const h = r.k_min_clearing25;
  return ckShort(nm) + " (from k = " + ckSci(h.k_M) + " M⁻¹ s⁻¹, " + h.reactor.replace(/ \d+ rpm| \(25 um gap\)/, "").toLowerCase() + (h.at_substrate_cap ? ", at its substrate cap" : "") + ")"; }).join("; ");
// The Ni-XEC row's recirculating-flow cell across the band: the third reading of the Table S5
// discrepancy, computed from the sweep. Named by reaction and reactor, never by position.
const ckXec = () => {
  const r = srRow("Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)");
  if (!r) return "";
  return "At the sourced k = 10² M⁻¹ s⁻¹ (§S5.7) the row's recirculating-flow ceiling is " + r.i_mAcm2.flow.toFixed(1) + " mA cm⁻² (" +
    Math.min(r.i_at_band_lo.flow, r.i_at_band_hi.flow).toFixed(1) + "–" + Math.max(r.i_at_band_lo.flow, r.i_at_band_hi.flow).toFixed(1) +
    " across the measured bracket; " + r.i_k0_mAcm2.flow.toFixed(1) + " at k = 0), against the 10 mA cm⁻² the campaign ran at — a nominal density on a carbon-felt cathode whose three-dimensional area a planar film does not credit, so the agreement is indicative and is not claimed as a validation.";
};
// The wall census: how many finite-k cells end on a ramp wall, and how tight those walls are.
const ckWalls = () => {
  const w = CK.walls; if (!w) return "";
  return w.wall_cells + " of the " + w.finite_k_cells + " finite-k cells end on a Newton wall of the current ramp. Each is a lower bound, and each is tight: the concentration-control walk that follows reaches a plateau at which the exhausted species — the resting carrier, or the substrate where the reaction front detaches and the current runs above the carrier's own cap — is at no more than " + (100 * w.exhausted_fraction_max_walls).toFixed(2) + " % of its bulk value at the electrode (median " + (100 * w.exhausted_fraction_median_walls).toFixed(2) + " %; " + (100 * w.exhausted_fraction_max_all).toFixed(2) + " % over every finite-k cell), the same test §S5.2 applies to the mediated matrix. No cell reported below either threshold could reach it within its own tightness, so the census is decidable in every cell.";
};
// ONE sentence, used by every passage that states the catalyst result, so they cannot disagree.
const ckSentence = () => {
  if (!SR) return "The catalyst rows are carried at k = 0, the floor of the EC′ current (§S5.7).";
  const ni = srBy("Ni(I)bpy"), co = srBy("Co-H"), aw = srBy("own CV");
  const g = SR;
  const W = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven"];
  return "Seven of the eleven rows are carried at a rate constant measured for the step that consumes the substrate and transferred to the row as a declared choice (§S5.7): the " + W[ni.length] +
    " nickel rows at k = 10² M⁻¹ s⁻¹ (oxidative addition of an aryl bromide to Ni(I)-bipyridine, inside a measured bracket of 10¹–10⁴), the " + W[co.length] +
    " cobalt-hydride rows at 7 × 10² (hydrogen-atom transfer to an alkene) and the Co(salen) aza-Wacker row at 10 (bounded below 4 × 10¹ by its own voltammetry); the other " + W[g.n_floor] +
    " carry no measured constant and stay at k = 0, the floor of the EC′ current. At those values " + W[11 - g.rows_clearing25_anywhere] + " of the eleven clear 25 mA cm⁻² in no architecture" +
    (g.ten_of_eleven_holds_at_band.every(x => x) ? ", at both edges of every bracket" : "") +
    "; the seven sourced rows sit in the kinetic regime, where the reaction layer is already thinner than every film, so thinning the film from the unstirred to the rotating-cylinder archetype buys " +
    g.gain_sourced_min.toFixed(1) + "–" + g.gain_sourced_max.toFixed(1) + "× where the k = 0 treatment gave " + g.gain_floor_median.toFixed(0) +
    "×. The class is concentration-capped either way: by the carrier where the homogeneous step is slow, by the dilute substrate where it is fast" +
    (ckCsRange ? " (substrates at " + ckCsRange[0].toFixed(3).replace(/0+$/, "").replace(/\.$/, "") + "–" + ckCsRange[1].toFixed(2) + " M)" : "") + ".";
};
const ckBandSentence = () =>
  "Re-solved over the whole declared band, " +
  (ckKfail === null
    ? "no catalyst row clears 25 mA cm⁻² at any k up to " + ckSci(ckKmax) + " M⁻¹ s⁻¹"
    : "the ten-of-eleven result holds for k ≤ " + ckSci(ckKhold) + " M⁻¹ s⁻¹ and fails at k = " + ckSci(ckKfail) +
      " M⁻¹ s⁻¹" + (ckKfail === ckKmax ? "" : "; by k = " + ckSci(ckKmax)) + ", " + ckN25(ckKmax) + " of the eleven clear 25 mA cm⁻²") +
  "; the largest amplification in the band is " + ckAmp.toFixed(1) + "× and " + ckAt(ckKmax).cells_at_substrate_cap + " of the " + ckAt(ckKmax).cells + " cells sit at their substrate cap at its top.";

// ---- rate-constant sweep (results/rate_constant_sensitivity.json, G-KSENS) ---------------------
const KS = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "rate_constant_sensitivity.json"), "utf8"));
const ksShort = (n) => n.replace(/ \(.*$/, "").replace(" -> ", " → ");
const ksList = () => KS.summary.rows_crossing_25.map(n => {
  const cases = KS.rows.filter(r => r.reaction === n && r.cells_crossing_25 > 0)
    .map(r => (r.factor > 1 ? "×10" : "÷10") + ", " + ["one","two","three","four","five","six","seven"][r.cells_crossing_25 - 1] + (r.cells_crossing_25 === 1 ? " architecture" : " architectures"));
  return ksShort(n) + " (" + cases.join("; ") + ")";
}).join("; ");
if (!ZS.rows.every(r => r.counts_unchanged)) throw new Error("Table S2 caption says no count moves under any alternative carrier charge, but the charge sweep disagrees");
// Sentence-initial counts are spelled out (a caption must not open with a numeral); the count itself is derived.
const numWordCap = (n) => (["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"][n] ?? String(n));
const sciD = (v) => { const e = Math.floor(Math.log10(v)); return (v / 10 ** e).toFixed(1) + " × 10" + String(e).replace("-", "⁻").replace(/\d/g, d => "⁰¹²³⁴⁵⁶⁷⁸⁹"[d]); };
const udMax = 100 * Math.max(...Object.values(UD.max_rel_change));   // percent
const udEffect = udMax === 0
  ? "leaves every one of the " + N_CELLS + " cells unchanged to the reported precision (the largest relative change is zero) and moves no threshold count in any architecture"
  : "moves no cell by more than " + sciD(udMax) + "% and no threshold count in any architecture";
const fcEnvLo = FC.sensitivity_um["h_5mm"] * FC.sensitivity_um["drho_1e-2"] / FC.delta_centre_um;
const fcEnvHi = FC.sensitivity_um["h_80mm"] * FC.sensitivity_um["drho_1e-3"] / FC.delta_centre_um;
const f2 = (x) => Number(x).toFixed(2);

const KT = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "figK_kappaT_sensitivity.json"), "utf8"));
const ktPair = (reactor, solvent) => {
  const d = (KT.brackets[reactor] || {})[solvent];
  if (!d) throw new Error("figK_kappaT_sensitivity.json has no " + reactor + "/" + solvent);
  return d;
};
const KT_FLIPS = KT.verdict_flips || [];
if (KT_FLIPS.length === 0)
  throw new Error("S6.3 prose reports which verdicts the bracket reverses; the model reports none. "
                  + "Rewrite the paragraph rather than the number.");
const KT_FLIP = ktPair(KT_FLIPS[0].reactor, KT_FLIPS[0].solvent);

// ── the seven-archetype thermal table (2026-09-12) ────────────────────────────────────────────
// S6 used to be written around five reactors with four DECLARED design currents. It now runs on
// Figure 5's own seven archetypes plus the zero-gap reference, each judged against the median
// limiting current the published matrix computes for it, so every number below is interpolated
// from the model's artifacts rather than typed.
const THERM = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "figK_thermal.json"), "utf8"));
const TGEO = JSON.parse(fs.readFileSync(
  path.join(__dirname, "results", "thermal_geometry_sensitivity.json"), "utf8"));
const T_ARCH = THERM.reactors.map(r => r.name);
const T_IDES = THERM.panelB._design_currents;
const T_CEIL = (sol, arch) => THERM.panelB[sol][arch];
const T_MARG = (sol, arch) => T_CEIL(sol, arch) / T_IDES[arch];
const T_U = Object.fromEntries(THERM.reactors.map(r => [r.name, r.U_passive]));
const T_GAP = Object.fromEntries(THERM.reactors.map(r => [r.name, r.gap_m]));
const T_SOLV = ["THF", "MeCN", "DMF", "aq. NaOH"];
const T_PRETTY = {"THF": "THF", "MeCN": "MeCN", "DMF": "DMF", "aq. NaOH": "aqueous NaOH"};
if (T_ARCH.length !== 7)
  throw new Error("S6 is written for the six preparative architectures plus the zero-gap reference; "
                  + "figK_thermal.json carries " + T_ARCH.length + " rows.");
// the architectures that share the beaker gap, read from the table rather than counted by hand
// ---- the S6 quantities the model emits rather than the prose typing them --------------------
// 2026-09-12: five S6 sentences carried numbers the reactor table had moved past (the drop from
// the assumed 0.02 W cm-2 K-1 read "~9%" where the model gives 15-16%, and the wetted-area pairs,
// the h_ext cancellation and the worked example had all been computed on retired inputs).
const TSUP = THERM.si_support;
const _pct = (x) => (100 * x).toFixed(0) + "%";
const _sorder = ["THF", "MeCN", "DMF", "aq. NaOH"];
const _drop = (from, to) => _sorder.map(x => 1 - TSUP.beaker[x][to] / TSUP.beaker[x][from]);
const _rng = (v) => {
  const lo = Math.min.apply(null, v), hi = Math.max.apply(null, v);
  const a = (100 * lo).toFixed(0), b = (100 * hi).toFixed(0);
  return a === b ? a + "%" : a + "\u2013" + b + "%";
};
const ASSUMED_DROP = _rng(_drop("at_assumed_U", "at_geometric_U"));
const WETTED_DROP = _rng(_drop("at_geometric_U", "at_wetted_sigma"));
const WETTED_PAIRS = _sorder.map(x => T_PRETTY[x] + " " + TSUP.beaker[x].at_geometric_U.toFixed(0)
  + " \u2192 " + TSUP.beaker[x].at_wetted_sigma.toFixed(0)).join(", ");
const HEXT_RISE = _pct(TSUP.beaker.DMF.at_hot_h_ext / TSUP.beaker.DMF.at_geometric_U - 1);
const BOTH_PAIR = TSUP.beaker.DMF.at_geometric_U.toFixed(0) + " \u2192 "
  + TSUP.beaker.DMF.at_wetted_sigma_and_hot_h_ext.toFixed(0);
const EX_ECELL = TSUP.worked_example.E_cell_V;
const EX_OHMIC = TSUP.worked_example.ohmic_V;
const EX_Q = TSUP.worked_example.q_Wcm2;
const EX_TSS = TSUP.worked_example.T_ss_C;
// the external film's share of the series resistance, across the architectures the model carries
const _SHARE = THERM.reactors.map(r => (1 / THERM.h_ext_Wm2K) / (1 / r.h_int + 1 / THERM.h_ext_Wm2K));
const EXT_SHARE = (100 * Math.min.apply(null, _SHARE)).toFixed(1) + "\u2013"
                + (100 * Math.max.apply(null, _SHARE)).toFixed(1) + "%";
const N_THERM_ROWS = census(CAT("Thermal model")).n;
// the kappa(T) bracket, read per reactor and solvent rather than typed
const KT_BEAKER = T_ARCH[0], KT_MICRO = T_ARCH.filter(a => /microfluidic/.test(a))[0];
const ktCeil = (reactor, solvent) => ktPair(
  reactor === KT_MICRO ? "microfluidic 25 um" : reactor, solvent);

const T_SIGMA = (a) => THERM.reactors.find(r => r.name === a).sigma;
// kappa-axis reversal points and the NaI/DMF beaker example, emitted by figs/make_figK.py
// (2026-09-14). The SI typed 12.9x, 20.0x, 2.05x, 1.27x, 187 C and U' = 0.0144 on the retired
// sigma = 12.5 and they outlived the derivation of sigma = 9.96 by a day.
const TFL = TSUP.kappa_flips;
const DMFX = TSUP.beaker_dmf_example;
const ARCH_SHORT = (a) => a.replace("RDE 1600 rpm", "rotating disc").replace("rotating cyl. 3000 rpm", "rotating cylinder")
  .replace(/microfluidic.*/, "microfluidic chip").replace("zero-gap PEM stack", "zero-gap stack");
const T_PREP = (sol) => Object.entries(TFL[sol]).filter(([a]) => !/zero-gap/.test(a));
const T_BIND = (sol) => T_PREP(sol).filter(([, v]) => !v.passes).sort((x, y) => x[1].multiple - y[1].multiple)[0];
const T_PASSMULT = (sol) => T_PREP(sol).filter(([, v]) => v.passes).map(([, v]) => v.multiple);
const xmul = (x, d = 1) => Number(x).toFixed(d) + "×";
const U_UNST = T_U[T_ARCH[0]], U_STIR = T_U[T_ARCH[1]];
const SIG_B = T_SIGMA(T_ARCH[0]);
const DMF_TSS_FOLD = DMFX.kappa_Tss_at_boil_mScm / (DMFX.kappa_S_per_m * 10);
const DMF_BIND = T_BIND("DMF"), THF_BIND = T_BIND("THF"), MECN_BIND = T_BIND("MeCN");
const THF_RCE = TFL.THF["rotating cyl. 3000 rpm"].multiple;
const NAOH_MARG = T_PREP("aq. NaOH").map(([, v]) => v.margin);
const NAOH_RANGE = Math.min.apply(null, NAOH_MARG).toFixed(1) + "–" + Math.max.apply(null, NAOH_MARG).toFixed(1) + "×";
const DMF_BAND_TOP = 16.0;
const DMF_BIND_IN_BAND = DMF_BIND[1].kappa_reverse_mScm < DMF_BAND_TOP;
const THF_PASS_LO = Math.min.apply(null, T_PASSMULT("THF")), THF_PASS_HI = Math.max.apply(null, T_PASSMULT("THF"));
const MCP_DMF_100 = 194;   // J K-1: 100 mL DMF (rho 0.944 g mL-1, c_p 2.06 J g-1 K-1), as stated in S6
const TAU_MIN = (mL) => MCP_DMF_100 * (mL / 100) / (THERM.volume_sweep.U_passive[String(mL)] * 10) / 60;
const T_SHARED = T_ARCH.filter(a => Math.abs(T_GAP[a] - T_GAP[T_ARCH[0]]) < 1e-12);
const T_FAILS = (sol) => T_ARCH.filter(a => T_MARG(sol, a) < 1);
const f1 = (x) => Number(x).toFixed(1);
for (const grp of ["thermal", "transport"]) {
  if (!BOUNDS[grp] || BOUNDS[grp].status) {
    throw new Error("si_sensitivity_bounds.json is incomplete (" + grp + ": " +
      (BOUNDS[grp] ? BOUNDS[grp].status : "missing") + "). Re-run data/si_sensitivity_bounds.py; " +
      "the band-edge mediated solves julia/_bounds_lo.jl and _bounds_hi.jl must both be complete.");
  }
}
const bnum = (x) => (Math.abs(x) >= 100 ? x.toFixed(0) : Math.abs(x) >= 10 ? x.toFixed(1) : x.toFixed(2));
const ARCHLBL = { natural: "unstirred batch", stirred: "stirred batch", flow: "recirculating flow cell",
                  anec: "ANEC flow cell", micro: "microfluidic cell", rde: "RDE 1600 rpm", rce: "rotating cylinder" };

let LEDGER = null;
try {
  LEDGER = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "assumption_ledger.json"),
                                      "utf8"));
  // The SI reports the PUBLISHED subset, so it must use the ledger's live counts.
  if (LEDGER.n_assumption_live == null) {
    throw new Error("assumption_ledger.json predates the liveness split; re-run "
                    + "data/registry_liveness.py then figs/analysis_assumption_ledger.py");
  }
  if (LEDGER.n_assumption_live !== CENSUS_ALL.assumption) {
    throw new Error("ledger counts " + LEDGER.n_assumption_live + " live assumption rows but the "
                    + "published registry has " + CENSUS_ALL.assumption
                    + "; re-run data/registry_liveness.py then figs/analysis_assumption_ledger.py");
  }
} catch (e) {
  if (!/ENOENT/.test(String(e))) throw e;
  LEDGER = null;
}

// ---------- content ----------
const letter = { size: { width: 12240, height: 15840 } };
const CTR = AlignmentType.CENTER;
const sup = (t) => new TextRun({ text: t, size: 24, superScript: true });
const front = [
  // Title page, matching the manuscript's: same title, same subtitle, same author list and
  // affiliations, same corresponding-author line and date.
  new Paragraph({ alignment: CTR, spacing: { before: 1400, after: 200 },
    children: [new TextRun({ text: "Supporting Information", size: 36, bold: true })] }),
  new Paragraph({ alignment: CTR, spacing: { after: 140 },
    children: [new TextRun({ text: "Reaction engineering for electrified organic synthesis", size: 30, bold: true })] }),
  new Paragraph({ alignment: CTR, spacing: { after: 420 },
    children: [new TextRun({ text: "Perspective for the 10th Anniversary of Reaction Chemistry & Engineering", size: 24 })] }),
  new Paragraph({ alignment: CTR, spacing: { after: 220 }, children: [
    new TextRun({ text: "Justin C. Bui", size: 24 }), sup("1,2,†"),
    new TextRun({ text: ", Alexandria X. Lam", size: 24 }), sup("2"),
    new TextRun({ text: ", Jonas Rein", size: 24 }), sup("1"),
    new TextRun({ text: ", Kasie Leung", size: 24 }), sup("1,3"),
    new TextRun({ text: ", Connor W. Coley", size: 24 }), sup("1"),
    new TextRun({ text: ", Klavs F. Jensen", size: 24 }), sup("1,†") ] }),
  new Paragraph({ alignment: CTR, spacing: { after: 160 }, children: [
    sup("1"), new TextRun({ text: " Department of Chemical Engineering, Massachusetts Institute of Technology, Cambridge, MA 02139, USA; ", size: 20 }),
    sup("2"), new TextRun({ text: " Department of Chemical and Biomolecular Engineering, NYU Tandon School of Engineering, Brooklyn, NY 11201, USA; ", size: 20 }),
    sup("3"), new TextRun({ text: " Department of Chemistry and Chemical Biology, Harvard University, Cambridge, MA 02138, USA", size: 20 }) ] }),
  new Paragraph({ alignment: CTR, spacing: { after: 420 }, children: [
    new TextRun({ text: "† Co-corresponding authors: J. C. Bui (jcbui@mit.edu), K. F. Jensen (kfjensen@mit.edu)", size: 20 })] }),
  // 2026-09-29: the author edited the SI title page in his own copy of the condensed build -- the
  // month, and the removal of the descriptive subtitle, which the MANUSCRIPT's title page does not
  // carry either (its second line is the anniversary note). Ported here because the SI is a build
  // output: left in the .docx alone, the next rebuild would have destroyed both.
  new Paragraph({ alignment: CTR, spacing: { after: 600 },
    children: [new TextRun({ text: "September 2026", size: 24 })] }),
  new Paragraph({ children: [new PageBreak()] }),

  h1("S1. Model overview"),
  h2("S1.1 Modelling assumptions"),
  p("Four modelling choices define the scope of this analysis. Each is stated together with the sensitivity bound used to evaluate its effect, and all four are registered in Table S7c and tested by a named check."),
  p("(i) The transport problem is solved on dilute-solution theory: Nernst\u2013Planck fluxes with a "
     + "constant diffusivity per species, local electroneutrality, unit activity coefficients, and no "
     + "Stefan\u2013Maxwell cross-coefficients (Newman, Ch. 11). This treatment is necessary because the Onsager/Stefan\u2013Maxwell coefficients required by concentrated-solution theory are unavailable for these fifty organic electrolyte compositions. Its consequences can be estimated from measured concentration-dependent conductivity. Dilute theory with concentration-independent mobilities predicts \u03ba \u221d c, i.e. a "
     + "constant equivalent conductance, and the 21-point isotherms of Dorn et al. show \u039b falling to "
     + "0.44 of its dilute value by 0.80 mol kg\u207b\u00b9 and to 0.05 by 4.50 mol kg\u207b\u00b9 for "
     + "Bu\u2084NBF\u2084/MeCN, and to 0.74 by 1.57 mol kg\u207b\u00b9 for aqueous NaCl. The dilute approximation therefore becomes quantitatively inaccurate above roughly 1 M."),
  p("The influence of concentrated rows can be isolated by splitting the fifty reactions at 1 M "
     + "total dissolved concentration (c = carrier + substrate + supporting electrolyte). This "
     + "division gives "
     + DS.strata.concentrated.n + " concentrated rows and "
     + DS.strata.dilute.n + " dilute rows, and concentration affects the two groups differently. Because i_lim \u221d C, "
     + "concentration raises the ceiling and degrades the theory at the same time, and the two are "
     + "correlated across the set. Of the " + DS.strata.all.n25[0] + " reactions that clear "
     + "25 mA cm\u207b\u00b2 in the unstirred beaker, " + DS.strata.concentrated.n25[0] + " are "
     + "concentrated rows, though those are only "
     + Math.round(100 * DS.strata.concentrated.n / DS.strata.all.n) + "% of the set; within the "
     + "dilute stratum alone the count is " + DS.strata.dilute.n25[0] + " of "
     + DS.strata.dilute.n + ". The dependence weakens as the reactor improves; at the RCE "
     + "the same share is " + DS.strata.concentrated.n25[DS.architectures.indexOf("rce")] + " of " + DS.strata.all.n25[DS.architectures.indexOf("rce")] + " "
     + "because there the ceiling is set by the hydrodynamics rather than by how much "
     + "material is dissolved. Two comparisons bound this sensitivity. The ordering " + ORDERING_TEXT
     + ", holds inside the dilute stratum on its own and inside the "
     + "concentrated stratum on its own, so no conclusion this Perspective draws depends on which "
     + "stratum a reaction falls in; and the departure measured above is an "
     + "**electrolyte** effect, whereas the most concentrated entry in the set, acrylonitrile hydrodimerization at 13.70 M total, carries no supporting electrolyte. On "
     + "supporting-electrolyte molarity the split is "
     + DS.by_electrolyte_molarity["elyte >= 1 M"].n + " rows at \u2265 1 M against "
     + DS.by_electrolyte_molarity["elyte <  1 M"].n + " below it, and the ordering holds in both. "
     + "Threshold counts for the concentrated stratum therefore carry the greatest uncertainty."),
  p("(ii) The viscosity is the pure solvent's, not the solution's. \u03bc in Table S3 is the "
     + "page-anchored CRC value for the neat solvent, used both in Wilke\u2013Chang (D \u221d 1/\u03bc) "
     + "and in \u03bd = \u03bc/\u03c1 for the mass-transfer correlations, while the cells contain solute "
     + "at up to 13.7 M total. A solution is more viscous than the solvent it is made from, so every "
     + "affected ceiling is overstated. Because solution-viscosity measurements are unavailable for these fifty compositions, we instead sweep the ratio (\u00a7S10). The first "
     + "\u226525 mA cm\u207b\u00b2 count moves at \u03bc_solution/\u03bc_solvent = 1.5, and it is the "
     + "unstirred column that moves; the architecture ordering survives to 3.0, and the thin-gap, RDE "
     + "and RCE counts do not move anywhere in that range."),
  p("(iii) The model computes a ceiling, not an operating point. There is no electrode kinetics in the "
     + "transport solve: no Butler\u2013Volmer term and no exchange current density (i\u2080 enters only "
     + "the thermal balance of \u00a7S6). Every current density reported here is the transport-limited "
     + "maximum, which a real cell approaches from below and never exceeds. Electrode kinetics are omitted because their rate constants are unavailable for most of the fifty electrode reactions."),
  p("(iv) The diffusion layer is a lumped parameter, not a solved boundary layer. \u03b4 is a measured film for the two flow "
     + "archetypes and comes from a mass-transfer correlation for the three remaining convective "
     + "ones; for the two batch archetypes it is a "
     + "measured proxy (stirred, 200 \u00b1 7 \u03bcm) and the free-convection correlation evaluated at a "
     + "declared electrode height and density driving force (unstirred, " + FC.delta_centre_um.toFixed(0)
     + " \u03bcm) (Table S1); the momentum equations are not solved. Because i_lim scales as 1/\u03b4, uncertainty in \u03b4 has the largest influence on the transport ceiling; Table S7g quantifies this effect for each batch-film estimate."),
  p("The numerical implementation is verified against analytic limits of the adopted theory: Newman's twofold migration enhancement for a binary electrolyte is reproduced to 0.5% and 0.26% (\u00a7S5.6), and discrete charge conservation holds to 3 \u00d7 10\u207b\u00b9\u00b2. Sensitivity analyses further show that none of the reported sweeps reverses the architecture ordering or the order-of-magnitude contrasts on which the conclusions depend. Individual threshold counts are less robust than this ordering, and \u00a7S10 reports their bounds."),
  p("We quantify the transport-limited current density accessible to organic electrosynthesis as a function of reactor architecture, for a set of 50 reactions chosen to represent the published literature. The analysis proceeds in stages. Stage 0 evaluates the Nernst diffusion-layer limiting current for every reaction in seven reactor archetypes: four whose film is a measured or derived constant and three described by established engineering correlations. Stage 1 resolves the diffusion film with a one-dimensional Nernst–Planck model under the electroneutrality constraint, which adds ionic migration, the film potential drop, and the supporting-electrolyte dependence that the Stage 0 picture omits. A companion module evaluates the ohmic cell-voltage stack and the associated Joule-heating ceiling. All calculations are implemented in Julia using the finite-volume, log-concentration, damped-Newton architecture of our CO2-reduction continuum model;«bui2022» the code is dependency-free (Julia standard library only) and archived with this SI."),
  p("Three conclusions follow. First, reactor architecture moves the transport ceiling by more than an order of magnitude: at the reported literature conditions of Table S2, the median limiting current across the 50 reactions rises from " + med("natural") + " mA cm⁻² in an unstirred batch cell to " + medI("flow") + " mA cm⁻² in a recirculating flow cell and to ≈" + medI("rce") + " mA cm⁻² at a turbulent rotating-cylinder electrode, and the number of reactions clearing an industrially relevant 25 mA cm⁻² rises from " + ge25("natural") + " to " + ge25("rce") + ". Second, the benefit is mechanism-dependent: 28 of the 31 substrate-carried electrolyses clear 25 mA cm⁻² in at least one architecture (the three exceptions are all deliberately dilute academic protocols at 0.02–0.08 M — a flow-kinetics study, the RAE-activated decarboxylative coupling whose electrolysis runs at 0.029 M, and a catalytic-in-electrons entry at 0.1 F mol⁻¹), whereas 10 of the 11 reactions whose current is carried by a dilute molecular catalyst (2.6–15 mM at the verified loadings) clear it in none — the single exception runs at 30 mM — and the 25 mM ACT mediator plateaus at 22 mA cm⁻² in every architecture. For that class the ceiling is set by concentration, not convection. " + ckSentence() + " Third, at the current densities that transport engineering makes available, the ohmic-heat term i²L/κ becomes the binding constraint in low-conductivity media unless the inter-electrode gap is reduced in proportion; thermal management, not solvent choice, sets the practical limit."),

  h1("S2. Stage 0: film model and mass-transfer correlations"),
  // NAMING. This SI numbers the three MODEL LAYERS Stage 0 / Stage 1 / Stage 2. Main-text
  // Section 3 numbers REACTOR CLASSES Tier 1 ... Tier 4. Both schemes previously used the
  // word "tier", so "Tier 1" and "Tier 2" each meant two unrelated things across the two
  // documents. "Stage" was chosen because "Level" collides with the TRL-E readiness levels
  // of Section 8 (11 uses) and "Layer" with the diffusion, boundary and reaction layers
  // (49 uses here). The CSV filenames keep the historical tier0_ spelling; renaming them
  // would touch every solver and gate that reads them, so the note below says so instead.
  p("Two numbering schemes appear in this work and they are unrelated. Here Stage 0, Stage 1 and Stage 2 name the three layers of the transport model \u2014 the film expression of Eq. S1, the Nernst\u2013Planck solver of \u00a7S5 and the EC\u2032 solver of \u00a7S5.4, in order of increasing physical detail. Section 3 of the main text uses Tier 1 through Tier 4 for classes of reactor ordered by diffusion-layer thickness. Tier always refers to a reactor and Stage always to a model layer. "),
  p("The limiting current density for a species that must reach the electrode to sustain the reaction is"),
  eqn([{m:[msub("i","lim"), mr("="), mfr([msub("n","c"), mr("F"), msub("D","c"), msub("C","c")], [mr("δ")])]}], "S1"),
  p("where D_c and C_c are the diffusivity and bulk concentration of the transport-limiting current carrier, n_c the electrons delivered per carrier turnover at the electrode, and δ the Nernst diffusion-layer thickness. We classify every reaction by its carrier: (i) direct electrolyses, in which the substrate itself exchanges electrons; (ii) mediated electrolyses, in which a redox shuttle (TEMPO/ACT, NHPI, halide, quinone) carries the current at its own concentration and n_c counts electrons per shuttle round trip; and (iii) molecular-catalyst electrolyses (Ni, Co, Mn, Cu, Rh), in which the electrode turns over the catalyst, present at 2.6–30 mM at the verified loadings. Equation S1 applied to the carrier, not the substrate, is the ceiling the matrix publishes for the second and third classes — for the mediated rows with the homogeneous step solved (§S5.4), for the catalyst rows at k = 0, which is the floor of the EC′ current and is opened up in §S5.7; this generalizes the mechanism–transport coupling demonstrated for three reactions by Oliver et al.«oliver2025»"),
  p("δ is obtained per reactor archetype from the correlations in Table S1, evaluated per species because δ depends on D and on the solvent kinematic viscosity ν. Where a correlation applies only above/below a flow-regime boundary we verified the regime (laminar Re < 2300 for the channel cells; the rotating-cylinder correlation is intrinsically turbulent)."),
  mkTable(
    ["Archetype", "Model", "Geometry / operating point", "Correlation", "Ref."],
    [["Unstirred batch", "natural-convection plateau", "vertical plate, quiescent", "δ = 228 μm (fixed)", "derived; the source's own diffusion-layer form δ = 1.48 x (Sc Gr)^−¼ (Eq. XVII) at a declared 20 mm height and Δρ/ρ = 3.2 × 10⁻³ (Wilke, Eisenberg & Tobias, J. Electrochem. Soc. 1953, 100, 513–523). Ref. ⟦bard⟧ defines δ₀ but tabulates no value."],
     ["Stirred batch", "fixed film", "planar electrode in a convecting cell", "δ = 200 μm (fixed)", "measured on a proxy system; 200 ± 7 μm by diffusion-limited current (Williams, Corbin, Zeng, Lazouski, Yang & Manthiram, Sustainable Energy Fuels 2019, 3, 1225–1232, p. 1227). Band 193–207 μm (Table S7g)"],
     ["Recirculating flow cell", "fixed film", "parallel-inlet recirculating H-cell, 280 μL s⁻¹", "δ = 106.9 μm (fixed)", "measured; ferricyanide limiting current on the cell itself (⟦watkins2023⟧, SI Table S1: 106.9 μm experimental, 242 μm by the authors' COMSOL model). Band ±12.1 % (Table S7g)"],
     ["ANEC flow cell", "fixed film", "recirculating analytical cell (ANEC), nebulised catholyte, 140 μL s⁻¹", "δ = 36.2 μm (fixed)", "measured; same method and table (⟦watkins2023⟧: 36.2 μm experimental, 57 μm COMSOL; the separate angled-inlet H-cell of the same table, whose bottom inlet faces the electrode at 20°, reads 33.4 μm). Band ±12.1 % (Table S7g)"],
     ["Microfluidic cell", "Lévêque entrance, half-gap floor", "gap 25 μm (0.001 in FEP spacer), τ = 4 min", "δ = h/2 = 12.5 μm for every row", "derived from the printed gap and residence time of ⟦mo2020⟧ (SI p. 13); the Lévêque group is 4h²/(Dτ) exactly, and it lies so far below the fully developed value that the half-gap film binds for all fifty rows (Table S7g)"],
     ["RDE", "Levich", "1600 rpm (declared)", "δ = 1.61 D^⅓ ν^⅙ ω^-½", "measured; coefficient 1.61 as printed by ⟦bard⟧ p. 30 fn. 11 (confirmed Sect. 12.4), origin ⟦levich⟧"],
     ["Rotating cylinder", "Eisenberg–Tobias–Wilke", "d 1.2 cm, 3000 rpm", "Sh = 0.0791 Re^0.70 Sc^0.356", "correlation measured ⟦eisenberg⟧; calibrated at Sc 2230–3650, Re 112–162,000 (p. 313)"]],
    [1400, 1350, 1800, 1900, 3270]),
  cap("Table S1. Reactor archetypes and mass-transfer correlations, with the provenance state of each entry (registry: Table S7g). δ is evaluated per species from its D and the solvent ν. Three qualifications belong here rather than in a footnote. The two batch archetypes are anchored differently, and the difference matters. The unstirred value rests on two declared inputs: Ref. ⟦bard⟧ contains no numerical δ for natural convection (§1.4.2 defines δ₀ and calls it \"often unknown\"; §4.4.2 gives only the √(2Dt) rule of thumb), so δ is derived instead from the diffusion-layer equation Wilke, Eisenberg & Tobias print for exactly this quantity, δ′ = 1.48 x (Sc Gr)^−¼, evaluated over each reaction's own ν and D at a declared electrode height and density driving force: " + FC.delta_centre_um.toFixed(0) + " μm, with an envelope of " + fcEnvLo.toFixed(0) + "–" + fcEnvHi.toFixed(0) + " μm over those two declarations. The driving force is the less innocent of the two, because at the limiting current it is set by the concentration the surface depletes and so differs from row to row; one value is declared for all fifty because the densification coefficients of these organic solutions are not available, and Table S7g gives the one case that can be page-anchored (2 M NaCl, for which the film would be " + FC.drho_rho_illustration.delta_um_at_central_height.toFixed(0) + " μm). An independent measurement of a natural-convection film at a millimetric electrode in quiescent solution, 230 ± 10 μm for 10 mM ferrocyanide in 1 M KCl, brackets that value. The stirred value is a measurement, δ = 200 ± 7 μm, but of a proxy system — dissolved O₂ in a gas-bubbled aqueous cell rather than an organic electrolyte under magnetic stirring — and what that proxy costs is stated in full in Table S7g. Both batch films are therefore central values, and the contrast between them is 1.14×. The two remain close, and the separation is bounded by a declared geometry rather than measured: the unstirred film exceeds the stirred one only for electrode heights above about 12 mm at the central driving force. The three flow films are anchored differently again: the two recirculating cells are measured films, obtained on the cells themselves by the same ferricyanide method as the stirred value but in aqueous electrolyte, and they are applied unscaled to every row, exactly as the stirred film is; the microfluidic film is derived from a printed gap and residence time by the Lévêque entrance solution bounded by the half-gap film, and for that cell the bound is what binds, so the film is the half-gap for every row and the Lévêque coefficient sets no reported number. And the rotating-cylinder correlation was fitted over Sc = 2230–3650 (p. 313), whereas the 50 reactions here span Sc = 176–19,006, so 49 of 50 rows sit outside the calibrated window — 44 of them below its floor, because aprotic organics raise D and lower ν together. Re-anchored at the centre of the calibrated range, the Sc^(1/3) asymptote raises the rotating-cylinder median rather than lowering it, so on this axis the column is an under-estimate rather than an upper one (§S3.3)."),

  h1("S3. Transport-property estimation"),
  h2("S3.1 Diffusivities"),
  p("Direct measurements of diffusion coefficients in the non-aqueous electrolytes used for organic electrosynthesis remain scarce (Section S8). We therefore estimate D for organic carriers with the Wilke–Chang correlation,«wilke1955»"),
  eqn([{m:[mr("D"), mr("="), mr("7.4×"), msup("10","−8"), mfr([msup(mrb([mr("φ"), msub("M","B")]), "1∕2"), mr("T")], [msub("μ","B"), msup(msub("V","A"), "0.6")])]}], "S2", "[cm² s⁻¹]"),
  p("with solvent molar mass M_B (g mol⁻¹), viscosity μ_B (cP), association factor φ (2.6 water, 1.9 methanol, 1.5 ethanol, 1.0 unassociated), and solute molar volume at the normal boiling point V_A (cm³ mol⁻¹) from Le Bas group contributions«poling» computed on the substrate SMILES (atomic increments C 14.8, H 3.7, O 7.4 (12.0 in acids), N 15.6/12.0/10.5 by substitution, S 25.6, halogens F 8.7/Cl 24.6/Br 27.0/I 37.0; ring corrections −11.5 (5-ring) and −15 (6-ring)). The canonical accuracy of Eq. S2 is ±10–20% for typical organics,«poling» but the available benchmark falls outside that band: against ferrocene/MeCN (measured 2.4×10⁻⁵ cm² s⁻¹) our implementation gives 1.8×10⁻⁵ cm² s⁻¹, −24%. The miss is in the direction and of the size reported for Wilke–Chang on compact organometallics, so it is not evidence of an implementation error; but it is the only independent measurement this model is tested against, and a single anchor that misses by more than the quoted band cannot be used to claim ±10–20% here. We therefore carry ±25% as the working property error below, which is what the sensitivity actually sweeps, rather than the canonical figure. Because i_lim is linear in D, a ±25% property error displaces log₁₀ i_lim by ±0.10, which is small relative to the order-of-magnitude spreads that separate reactor archetypes, and insufficient to move any conclusion in Table S5 except for entries already within ~25% of the threshold."),
  p("Three carrier types receive dedicated treatment. Small inorganic mediator ions (Br⁻, Cl⁻, SCN⁻), for which Wilke–Chang is invalid, use Nernst–Einstein diffusivities from limiting molar conductivities (D = λ°RT/z²F²).«crc,izutsu» Molecular catalysts use Stokes–Einstein with assigned hydrodynamic radii (4.0–5.0 Å for M(bpy)/M(salen) cores), consistent with the 3–7×10⁻⁶ cm² s⁻¹ range reported for such complexes in amide solvents. The lignin-valorization entry is carried by carbonate (Nernst–Einstein, λ° = 138.6 S cm² mol⁻¹, z = 2), reflecting the verified ex-cell architecture of that pilot process: the cell electrolyzes 1 M Na₂CO₃ to peroxodicarbonate on BDD and the lignin stream (0.1–3 wt% in 3 M NaOH) reacts downstream in an 80-L thermal reactor, never entering the cell.«ruecker2024»"),
    p("Supporting-electrolyte ions in solvents for which no limiting conductance is tabulated — " + UD.n_slots + " cation or anion slots across the fifty rows, " + UD.n_pairs + " distinct ion–solvent pairs, summarised in Table S7d — carry class defaults, " + sciD(parseFloat(prows.find(r => r[pcol("parameter")] === "Bu4N+/Q+ (organic)")[pcol("value")])) + " m² s⁻¹ for a cation and " + sciD(parseFloat(prows.find(r => r[pcol("parameter")] === "BF4-/generic A- (organic)")[pcol("value")])) + " for an anion, the values adopted for Bu₄N⁺ and BF₄⁻ in acetonitrile. Because a supporting ion carries no flux under local electroneutrality, this assigned diffusivity shapes the potential profile but does not enter the limiting current. Re-solving the full " + N_CELLS + "-cell Nernst–Planck layer with every such value divided and then multiplied by three " + udEffect + " (Table S7d)."),
h2("S3.2 Solvents and electrolytes"),
  mkTable(["Solvent", "M (g/mol)", "μ (mPa·s, 25 °C)", "ρ (g/mL)", "φ", "Source"],
    // The typed numbers below are NOT the source of Table S3 -- fromCSV() overwrites each one
    // from solvents.csv and records any disagreement in TABLE_DRIFT. They are a display-precision
    // string AND a tripwire. That only works while the list is clean: four entries had been
    // drifting permanently (MeCN mu 0.343, DMA mu 0.945, HFIP M 168.0 and mu 1.650), so every
    // build printed four warnings and a FIFTH, new one would have read as more of the same.
    // Re-sync a typed value whenever the registry moves, or the tripwire stops being one.
    [["MeCN","41.05","0.369","0.776","1.0","CRC"],["MeOH","32.04","0.544","0.786","1.9","CRC"],["DMF","73.09","0.794","0.944","1.0","CRC"],["DMA","87.12","1.927","0.937","1.0","CRC"],["THF","72.11","0.456","0.883","1.0","CRC"],["H2O","18.02","0.890","0.997","2.6","CRC"],["HFIP","168.04","1.619","1.596","1.0","lit."],["acetone","58.08","0.306","0.784","1.0","CRC"],["MeNO2","61.04","0.620","1.137","1.0","CRC"],["MeCN/H2O 9:1 v/v","36.4","0.48","0.82","1.17","lit. mixture μ; φM by P–G"],["MeOH/H2O 1:1 v/v","26.4","1.60","0.87","1.94","CRC mixture μ; φM P–G"],["H2O/MeCN 2:1 v/v","24.0","0.90","0.94","1.916","lit. mixture μ; φM Eq. S30"],["DMSO/THF 5:1 v/v","77.1","1.55","1.06","1.00","blend est.; φM P–G"],["tAmOH/H2O 3:1 v/v","35.0","2.80","0.85","1.73","blend est.; φM P–G"],["AcOH/HCOOH 1:1 v/v","53.0","1.28","1.13","1.0","blend of CRC endpoints"]].map(r => fromCSV(r, [[1,"M",null],[2,"mu",null],[3,"rho",null],[4,"phi",null]], solvRow, "S3")),
     [1700,1200,1600,1100,800,1800]),
  cap("Table S3. Solvent properties used in Eq. S2 and in ν = μ/ρ for the reactor correlations (full registry with per-entry provenance and state: Table S7b). Two things about this table must be read literally. First, only the product φM enters Eq. S2 — M and φ are never used separately — so for the mixtures the tabulated M is not a molar mass but one half of a presentational split of a single Perkins–Geankoplis product (ref. ⟦poling⟧, Eq. 11-9.8); the mixture entries 36.4, 26.4, 33.0, 56.0, 77.1, 35.0, 53.0 and 24.0 g mol⁻¹ should not be read as molecular weights. Second, the pure-solvent μ and ρ are measured, page-anchored to the CRC 97th edition tables of viscosity (pp. 6-243 to 6-247) and of laboratory solvent densities (pp. 15-13 to 15-20), and water to the IAPWS formulations; and one mixture is now derived: H₂O/MeCN 2:1 v/v is 28.0 wt% MeCN, inside the range measured by Ansari and Singh (Res. J. Chem. Sci. 2022, 12(1), 67–69, Table-1, p. 68), whose 20 and 30 wt% rows interpolate to η = 0.922 mPa s and ρ = 0.942 g mL⁻¹ against the 0.90 and 0.94 carried here. The remaining mixtures and both HFIP entries are assumptions. MeCN/H₂O 9:1 v/v is 87.5 wt%, outside that measured range, but is now bracketed by two of its measured points (η between 0.346 and 0.574 mPa s) rather than by nothing. For the others no isotherm reproducing them at 25 °C and the stated volume ratio could be opened. The CRC concentrative-properties tables, the obvious candidate for the aqueous mixtures, are tabulated at 20 °C and indexed by mass per cent, so they cannot support a 25 °C value at a volume ratio and are not cited for one. Because i_lim is linear in D and D ∝ 1/μ, a ±25% error in any of these displaces log₁₀ i_lim by ±0.10, which is small against the order-of-magnitude spreads separating the archetypes."),
  mkTable(["Electrolyte", "κ (mS/cm)", "State", "Margin before a stated conclusion flips", "Note"],
    [["3.0 M LiBr / THF","3.0","assumption",xmul(THF_BIND[1].multiple) + " (binding verdict, " + ARCH_SHORT(THF_BIND[0]) + "), against a band top of 2.19×; 1.30× for the §S6.2 zero-gap sentence","§S6 THF entry. Ref. ⟦peters2019⟧ SM p. S15 page-anchors the 3.0 M composition, not κ; the value came from the row's own note that this is a heavily ion-paired ether medium. THF (ε = 7.6) has a Bjerrum distance of 3.7 nm, so association is essentially complete and κ cannot be derived either. Band 0.2–6.6 mS cm⁻¹, with a state-B hard floor of 0.206 mS cm⁻¹ obtained by ohmic differencing on the flow-Birch cell of Lee et al., Org. Process Res. Dev. 2022, 26, 2674–2684 (R_tot ≤ V/I = 3.2 V / 0.520 A in a coaxial annulus whose geometry follows from the stated 17.8 mL annulus volume). Judged against each architecture's own transport ceiling, the binding verdict is the " + ARCH_SHORT(THF_BIND[0]) + ", which reverses only at " + xmul(THF_BIND[1].multiple) + " the carried conductivity against a band whose top is 2.19×. The §S6.2 zero-gap sentence is tighter, at 1.30×, and is quoted with that margin where it appears. Across the 0.2–6.6 band the verdicts do not turn: the microfluidic chip clears at every point and both rotating cells and the stack fail at every point; only the three centimetre-gap cells move, falling to their own transport ceilings at the state-B floor."],
     ["0.25 M Bu4NBF4 / MeCN","19.95","measured",xmul(MECN_BIND[1].multiple, 2) + " (binding verdict, " + ARCH_SHORT(MECN_BIND[0]) + "); " + xmul(TFL.MeCN["rotating cyl. 3000 rpm"].multiple, 2) + " at the rotating cylinder","§S6 MeCN entry. MEASURED: read off the raw κ(c) isotherm in the Supporting Information of Dorn, Kareth, Weidner and Petermann, J. Chem. Eng. Data 2024, 69, 1493–1502. An independent state-B route — Casteel–Amis (Casteel and Amis, J. Chem. Eng. Data 1972, 17, 55–59) applied to the fit the same article prints in Table 3, p. 1499 (κ_max 33.40 mS cm⁻¹, m̄_max 1.48127 mol kg⁻¹, a 0.78646, b −0.02156), with c → m̄ via M = 329.27 g mol⁻¹ and ρ(MeCN) = 0.7768 g cm⁻³ giving m̄ = 0.347 — returns 18.9 mS cm⁻¹. The two agree to 5.6%, which is the error a fit-and-invert reconstruction carries here; the measurement is the value adopted because it is the datum the fit was made from. Cross-checked at 1 M against Gong, Fang, Gu, Li and Yan, Energy Environ. Sci. 2015, 8, 3515–3530, Table 3, p. 3519 (32.75 derived vs 32.3 tabulated, +1.4%). Band 15–23 mS cm⁻¹. A mass-action bound of 24–36 mS cm⁻¹ is not used: it is a Lee–Wheaton extrapolation some 25× above its own fitted range."],
     ["0.2 M NaI / DMF","8.77","derived",xmul(DMF_BIND[1].multiple, 2) + " (binding verdict, " + ARCH_SHORT(DMF_BIND[0]) + (DMF_BIND_IN_BAND ? ", inside the 4–16 band" : "") + "); " + xmul(DMF_TSS_FOLD, 2) + " for the §S6 steady-state sentence","§S6 DMF entry, and the most exposed number in the registry. λ°(Na⁺) = 29.81 and λ°(I⁻) = 52.11 S cm² mol⁻¹ in DMF at 25 °C are page-anchored to Gopal and Jha, Indian J. Chem. 1977, 15A, 80–83, Table 2, p. 81, giving Λ°(NaI, DMF) = 81.9 ± 0.8 by Kohlrausch additivity, which corroborates to 0.7% the direct measurement Λ° = 81.35 ± 0.04 (Krumgalz and Barthel, Z. Phys. Chem. 1984, 142, 167–178, Table 2) that is the value adopted — and with it a hard ceiling κ ≤ cΛ° = 16.27 mS cm⁻¹. Λ(c) at 0.2 M has never been measured for this salt in this solvent, so the attenuation is transferred instead: Dorn's Supporting Information measures NaI in methanol across the full range, and with Λ°(NaI, MeOH) = 107.86 the measured Λ/Λ° at 0.2 M is 0.539, giving κ = 0.2 × 81.35 × 0.539 = 8.77 mS cm⁻¹. The single assumption — equal attenuation at equal molarity — is known to err in one direction, since DMF's higher permittivity (36.7 against 32.7) means it pairs less, so 8.77 is a floor rather than a best estimate; calibrating the Onsager limiting law on that same methanol measurement gives 9.72 mS cm⁻¹ as the better estimate. The floor is carried because its derivation is the shorter of the two. An independent third route using only same-system measurements — Krumgalz and Barthel's own association constant K_A = 7.50 dm³ mol⁻¹ with Debye–Hückel activity coefficients and Onsager relaxation — gives 8.30 mS cm⁻¹, within 5% of the adopted value. The " + ARCH_SHORT(DMF_BIND[0]) + " verdict and the two sentences of §S6 that rest on this row are quoted with their margins."],
     ["1 M NaOH (aq)","174.5","measured",NAOH_RANGE,"§S6 aqueous reference. The applicable CRC table is not p. 5-74 (Vanýsek, equivalent conductivity, 25 °C, c ≤ 0.1 M, whose NaOH row stops at 0.01 M). CRC Section 5 also carries \"Electrical Conductivity of Aqueous Solutions\" at p. 5-71 (20 °C, 0.5–50 mass %), which reaches every concentrated aqueous row here. Derived: c ↔ mass % from \"Concentrative Properties of Aqueous Solutions\" (20 °C; 1.000 M NaOH = 3.840 mass %), κ(mass %) from p. 5-71 (NaOH 2% = 93.1, 5% = 206 mS cm⁻¹) → 162–166 mS cm⁻¹ at 20 °C, corrected 20 → 25 °C at α = 1.5–1.9%/K for hydroxides → 174–182. Band 174–182, centred on 178; the adopted measurement of 174.5 sits just below its lower edge, which corroborates it. Pipeline validated against ASTM D 1125-95(2005) Table 1 Reference Solution A (1 demal KCl, 7.11352 mass %, 111.342 mS cm⁻¹ at 25 °C) to within +0.3 to +1.2%. Robust regardless (" + NAOH_RANGE + ")."],
     ].map(r => fromCSV(r, [[1,"kappa",null],[2,"state",null]], elecRow, "S4")),
    [2200,750,900,1350,4800]),
  cap("Table S4. Ionic conductivities (25 °C) quoted in the ohmic and thermal analysis of Section S6, with the provenance state and per-row margin of the registry (Table S7f). Of the " + CENSUS_COND.n + " registered conductivities, " + CENSUS_COND.derived + " " + isAre(CENSUS_COND.derived) + " derived and " + nOf(CENSUS_COND.assumption, "an assumption", "assumptions") + " in the sense of §S9; " + (CENSUS_COND.measured ? CENSUS_COND.measured + " " + (CENSUS_COND.measured === 1 ? "reaches" : "reach") + " the measured state" : "none reaches the measured state") + ". Row by row: 0.25 M Bu₄NBF₄/MeCN, 1 M NaOH aq and 0.1 M Bu₄NBF₄/DMF are measured, the first two read off raw κ(c) isotherms in the Supporting Information of Dorn et al. 2024 and the third from Shinkle et al., J. Power Sources 2014, 248, 1299–1305, Table 1; 0.2 M NaI/DMF is derived, by transferring a measured attenuation Λ/Λ° onto a directly measured Λ° (Eq. S27 and §S9); and 3.0 M LiBr/THF remains an assumption, the one conductivity here with no source for its value. Each of the three measured rows is read off a raw isotherm rather than reconstructed from a limiting-conductivity table, for a reason that is specific and checkable: evaluated with the measured Λ° = 171.1 S cm² mol⁻¹ for Bu₄NBF₄/MeCN, the Onsager limiting law goes negative above 0.228 M, so no λ° table can supply κ across the 0.03–1 M range these architectures use. The tightest margin is the DMF entry, whose binding verdict reverses at " + xmul(DMF_BIND[1].multiple, 2) + " and whose §S6 steady-state sentence flips at " + xmul(DMF_TSS_FOLD, 2) + ". Two facts bound what that costs. First, κ enters no transport quantity — Eq. S1 and the Nernst–Planck and EC′ solvers use D, C, δ and z only — so " + (CENSUS_COND.n - N_COND_CONCLUSION) + " of the " + CENSUS_COND.n + " registered entries " + isAre(CENSUS_COND.n - N_COND_CONCLUSION) + " display-only, tabulated for scale and supporting no stated conclusion. Second, the four that carry a conclusion have individually computed margins, given above and in Table S7f, and every statement resting on one is qualified in §S6.1, §S6.2 and §S6.3 by that margin."),

  h2("S3.3 Extrapolation of the rotating-cylinder correlation"),
  p("Table S1 gives each archetype its correlation and its provenance. One of the four is applied "
     + "outside the range it was established over, and because it sets the column carrying the "
     + "most favourable numbers in this work we quantify the resulting uncertainty and its direction. Eisenberg, Tobias and Wilke state their own calibration on p. 313: "
     + "\u201ca Schmidt number variation of " + SX.cal_window[0] + " to " + SX.cal_window[1]
     + " and a Reynolds number range of 112.0\u2013162,000\u201d. The fifty rows here run "
     + "Sc = " + SX.sc_min.toFixed(0) + "\u2013" + SX.sc_max.toFixed(0) + " with a median of "
     + SX.sc_median.toFixed(0) + ", so " + SX.n_below + " of " + SX.n_total + " sit below the "
     + "fitted floor and only " + SX.n_above + " above the ceiling. The extrapolation is therefore "
     + "predominantly to low Schmidt number, not high: aprotic organics are low-Sc relative to "
     + "aqueous ferricyanide because their low viscosity raises D and lowers \u03bd together. The "
     + "Reynolds number at this operating point runs " + SX.re_lo.toFixed(0) + "\u2013"
     + SX.re_hi.toFixed(0) + ", inside the fitted range throughout."),
  p("We bound this extrapolation with a second independently fitted correlation. Jang and co-workers\u2019 gastight rotating-cylinder "
     + "cell\u00abjang2022\u00bb yields "
     + SX.alt_correlation.replace("Jang 2022 Eq. 7: ", "")
     + ", fitted independently to the same geometry and validated over Re = "
     + SX.alt_valid_Re[0].toFixed(0) + "\u2013" + SX.alt_valid_Re[1].toFixed(0)
     + " and Sc > " + SX.alt_valid_Sc_min.toFixed(0) + ". The two correlations divide this "
     + "problem between them and neither covers all of it: Eisenberg spans the Reynolds range "
     + "these reactors occupy and is extrapolated in Schmidt, while the second spans the "
     + "Schmidt range \u2014 all " + SX.alt_rows_in_Sc + " of " + SX.n_total + " rows lie "
     + "inside it \u2014 and is extrapolated in Reynolds, where only " + SX.alt_rows_in_Re
     + " of " + SX.n_total + " lie inside. Eisenberg is retained as the primary correlation "
     + "because the Reynolds exponent is the stronger of the two (0.70 against "
     + SX.fitted_p + "), because it covers this operating point completely, and because it is "
     + "the standard correlation for the geometry; the second is used as the bound."),
  p("The difference between the correlations provides a direct bound on this uncertainty and exceeds the effect obtained by perturbing the fitted exponent. Per row the second correlation gives "
     + SX.factor_lo.toFixed(3) + "\u2013" + SX.factor_hi.toFixed(3) + "\u00d7 the current, "
     + "so the rotating-cylinder median falls from " + SX.medians.rce.toFixed(1) + " to "
     + SX.medians_alt.rce.toFixed(1) + " mA cm\u207b\u00b2 ("
     + (100 * (SX.medians_alt.rce / SX.medians.rce - 1)).toFixed(0) + "%), the count clearing "
     + "25 mA cm\u207b\u00b2 goes " + SX.n25_rce + " \u2192 " + SX.n25_rce_alt + " of "
     + SX.n_total + " and the count clearing 50 goes " + SX.n50_rce + " \u2192 "
     + SX.n50_rce_alt + ", and the rotating-cylinder median falls below the rotating-disc value, "
     + "inverting that one adjacent pair. The unstirred-to-rotating span is "
     + (SX.medians.rce / SX.medians.natural).toFixed(1) + "\u00d7 under the primary "
     + "correlation and " + (SX.medians_alt.rce / SX.medians.natural).toFixed(1)
     + "\u00d7 under the second. **The broader architecture ranking is unchanged.** The four-step ordering \u2014 unstirred < stirred < recirculating flow < ANEC "
     + "\u2014 holds identically under both, and the three thin-film archetypes (microfluidic, RDE, "
     + "rotating cylinder) stay above all four under both. The rotating-cylinder column should therefore be read as carrying about a "
     + "thirty per cent correlation uncertainty, and no conclusion here rests on its exact "
     + "value or on its rank against the rotating disc."),
  h1("S4. Reaction set"),
  h2("S4.1 CAS dataset for main-text Figure 1"),
  p("The dataset plotted in main-text Figure 1 was assembled by a two-stage retrieval from CAS content through SciFinder. The two stages do different work, and neither alone is adequate: a keyword search alone admits documents that merely mention electrochemistry, while the filter alone inherits whatever chemical scope the indexing happens to cover."),
  p("**Stage 1, topic query.** The chemical space is bounded by the topic search"),
  new Paragraph({ spacing: { after: 40 }, indent: { left: 360 }, children: [new TextRun({ text: "(\"organic electrosynthesis\" OR \"electroorganic synthesis\" OR electrosynth* OR \"electrochemical organic synthesis\")", size: 18, font: "Consolas" })] }),
  new Paragraph({ spacing: { after: 40 }, indent: { left: 360 }, children: [new TextRun({ text: "AND (oxidation OR reduction OR coupling OR functionalization)", size: 18, font: "Consolas" })] }),
  new Paragraph({ spacing: { after: 40 }, indent: { left: 360 }, children: [new TextRun({ text: "NOT (CO2 OR nitrate OR NO3 OR \"carbon dioxide\" OR \"nitrogen reduction\" OR fuel cell OR semiconductor OR OLED OR photovoltaic)", size: 18, font: "Consolas" })] }),
  p("The exclusions remove adjacent electrochemistry — CO₂ and nitrate reduction, fuel cells, and semiconductor and optoelectronic device work — that would otherwise dominate the hit list without contributing organic transformations."),
  p("**Stage 2, reaction filter.** Within the Stage-1 results the Reactions view is opened and the CAS-curated “Electrochemical” reaction-notes filter applied, which restricts the set to records CAS has indexed as electrochemical transformations rather than documents that merely mention electrochemistry."),
  p("**Deduplication.** Records are deduplicated by CAS reaction number, the earliest reported year retained, giving the 25,941 distinct transformations the figure reports. A reaction appearing in several publications therefore contributes once, dated to its first report, which is what makes the per-year counts of Fig. 1a a record of first demonstration rather than of publication volume."),
  p("**Atom mapping.** Reactant and product structures are mapped with a transformer-based mapper, with stoichiometry repaired on both sides before mapping is trusted: product-side repair removes duplicate fragments by re-mapping with one fragment withheld and keeping whichever assignment leaves fewest unmapped atoms; reactant-side repair adds a reactant only when more than three heavy atoms are otherwise unaccounted for, choosing the reactant that minimises unmapped atoms on each side. A record is not carried forward if more than 30% of the heavy atoms on either side remain untracked."),
  p("**Classification.** Unreactive spectators and fully untracked fragments are stripped, and records whose product contains a heavy metal are dropped. The remainder are binned by the number of effective reactants and products and classified within each bin: one-to-one records give degenerate entries, isomerization, simple oxidation, simple reduction and functional-group intraconversion; two-to-one records give C–C, C–N, C–O and C–S bond formation and other bond formation; three-or-more-to-one records give multicomponent coupling. Halogenation and cyclization span more than one bin and are decided on their own criteria. Records forming two or more products are left unclassified, fewer than 500 in total. Three descriptors decide every class: the per-element heavy-atom and hydrogen composition difference with the full heavy-atom skeleton, the bond-order-agnostic neighbour multiset at each tracked atom, and the set of product bonds joining two tracked atoms with no counterpart in the reactants."),
  p("**Redox assignment.** The net redox change of the substrate ledger that stacks each bar of Fig. 1b is computed per reaction by summing formal oxidation-state changes over all mapped atoms, seeded at the reacting sites and expanded outward, with explicit corrections where redox is carried by a leaving group. 21,459 records carry the atom-mapped data the assignment requires and are the basis of that panel."),
  p("**Scale and readiness.** The dataset records what was run, not at what scale: no field in it reports mass, volume or throughput. No record is therefore assigned a readiness level individually, and the readiness distribution of main-text Figure 10a is not a classification of these 25,941 transformations. Its lowest tier is the dataset total; the tiers above it are counted independently, from the demonstrations at 20 g or more reported by Lehnherr and Chen«lehnherr2024», the kilogram-scale pharmaceutical programmes reported by Kelly et al.«kelly2026», and the commodity processes of main-text Table 1. The panel bounds how few transformations have been carried above bench scale, and that bound rests on those surveys rather than on the dataset."),
  p("**Operating current density.** The dataset does not report one either, and what its free-text reaction notes do carry cannot stand in for it. A current density \u2014 a current per unit electrode area \u2014 appears in " + DJ.n_stating_j + " of the " + DJ.n_records.toLocaleString("en-US") + " records, " + DJ.share_stating_j_pct.toFixed(1) + "\u00a0% of the set. Those are not " + DJ.n_stating_j + " observations: they carry only " + DJ.n_distinct_notes + " distinct note strings and " + DJ.n_distinct_values + " distinct values, because the index repeats one report\u2019s conditions across every reaction it lists from that report, one string recurring " + DJ.max_note_repeats + " times. The reason a density is so seldom recoverable is that reports give a current: a further " + DJ.n_current_only.toLocaleString("en-US") + " records (" + DJ.share_current_only_pct + "\u00a0% of the set) state one in mA with no electrode area, so no density follows from them. Among the records that do give a density, " + DJ.share_below_25_by_record_pct + "\u00a0% lie below 25\u00a0mA\u00a0cm\u207b\u00b2 (" + DJ.share_below_25_by_value_pct + "\u00a0% of the distinct values), which agrees with the surveyed processes (main-text Fig.\u00a01d)\u00abferretti2025\u00bb, but the subset is too small and too duplicated to characterise the set. The main text therefore reports a threshold rather than an average: the share below 25\u00a0mA\u00a0cm\u207b\u00b2 and the number of records it is drawn from."),
  h2("S4.2 Stratification against the dataset"),
  p("The set is stratified by the reaction-class distribution of our dataset of 25,941 SciFinder-confirmed electrochemical transformations (main text Fig. 1b), of which 21,459 carry the atom-mapped records the classifier scores. Each exemplar is assigned by applying that classifier's published decision rules to the named transformation, one row at a time (the classification record gives, for each row, the code path in the published classifier that decides it; the resulting class is carried in the cls column of the reaction table, the single source both this document and the figures read). Two of the fifty rows fall outside the comparison basis: the catalytic alkene isomerization, which main-text Fig. 1b does not plot, and one row the classifier leaves unlabelled, exactly as it leaves 925 dataset records unlabelled. Set share against dataset share for the remaining 48: " + stratShares() + ". Every populated class share matches within seven percentage points across the 48 entries the classifier places, and no class is unrepresented — multicomponent coupling, the sparsest, stands at 6.2% of the set against 6.3% of the dataset, carried by a diazo/thiol/alcohol difunctionalization,«yang2023nc» an alkenesulfonate synthesis from a cinnamic acid, SO₂ and an alcohol«chien2025» and the alkoxysulfonylation entry«mei2019», whose β-methoxy sulfone product incorporates the methanol and so makes it a three-component coupling rather than a two-component C–S formation. On that basis the set is approximately representative of the dataset. The residual gaps are a deliberate over-sampling of simple oxidations and reductions, the transformations for which verified concentrations and currents are most reliably reported, and a corresponding under-sampling of cyclization. It remains a stratified rather than a proportional sample. Neither bears on what the set is used for — every entry is verified individually (Table S2), and the architecture rankings and carrier-class conclusions rest on order-of-magnitude contrasts within each entry rather than on class proportions. One regime is represented by a single entry rather than by a class share: electrogenerated-acid/base chemistry run at substoichiometric charge, for which current density is not the productive constraint and the transport ceiling quantified here is not the operative limit. The 0.1 F mol⁻¹ radical-cation Diels–Alder entry stands for that low-charge, catalytic-in-electrons regime. The set also deliberately oversamples carrier-borne current — 19 of 50 entries (38%) are mediated or molecular-catalyst-carried, against a dataset floor of 25% (main text Fig. 1c) — because that is precisely the class for which this analysis shows the transport ceiling to be concentration-capped rather than convection-limited (by the carrier at slow homogeneous kinetics and by the substrate at fast, §S5.7). Within each class we selected named, citable exemplars spanning direct, mediated, and catalyst-carried mechanisms, anchored by the industrial and scaled benchmarks (adiponitrile hydrodimerization;«baizer1964» the BASF capillary-gap methoxylation;«us5507922» the kilogram-scale sulfone oxidation«bottecchia2022» and Ni-catalyzed cross-electrophile coupling«kelly2026»). A precise statement of where the conditions come from, since concentrations set i_lim linearly (Eq. S1). The SciFinder dataset does not supply them: a survey of the aggregated condition notes of 26,790 SciFinder records — a superset containing all 25,941 entries in this dataset — finds molar concentration strings in 0.0% of records and named solvents in 0.6% (currents/controls, by contrast, in 52.9% — reaction databases record what was run, not at what concentration). The dataset therefore fixes only the class stratification of the set. Every concentration, solvent, and electrolyte in Table S2 was instead verified directly against the primary-source PDF of its named exemplar: for each row, the stated amounts and solvent volumes of the paper's standard/scaled conditions (table footnote, figure caption, or experimental section — the anchor is quoted in the final column of Table S2) were converted to molarity by explicit mmol/mL arithmetic. Forty-eight of the fifty rows are verified this way: forty against the main-article PDFs and patents, and eight more against their Supporting Materials (general-procedure mmol/mL arithmetic; SI page anchors in Table S2). Two are not, and both are declared rather than counted as verified: the amide α-methoxylation entry, which transfers the verified Shono carbamate conditions by stated analogy, and the Cl-mediated ethylene epoxidation, whose electrolyte is quoted verbatim from the exemplar (1.0 M KCl — the paper reads “a flow-cell setup with 1.0 M potassium chloride (KCl) electrolyte, in which ethylene was continuously sparged into the anolyte”) and whose substrate concentration is measured rather than estimated: ethene in 1.000 M KCl is 3.52 mmol L⁻¹, from the IUPAC Solubility Data Series vol. 57 (original measurement Yano, Suetaka, Umehara and Horiuchi, Kagaku Kogaku 1974, 38, 320–323), against 4.83 mmol L⁻¹ in pure water — a 27% salting-out correction that a plain Henry's-law figure omits. The Birch entry is anchored to its Supporting Material's scale campaigns:«peters2019» the 100-g flow run electrolyzes 0.18 M substrate in 3.0 M LiBr/THF with 12 equiv DMU and no TPPA (SM pp. S21–22; the 0.1-mmol general procedure runs 0.029 M with 0.21 M LiBr, SM pp. S12–13). The remaining row, the amide α-methoxylation entry, transfers the verified Shono carbamate conditions«shono1975» by stated analogy. The BASF methoxylation — whose monograph chapter could not be consulted (the supplied Organic Electrochemistry 4th-ed. scan ends at book p. 834, before Ch. 31, Pütter, pp. 1259–1308«puetter2001») — is instead verified against BASF's own process patents: US 5,507,922«us5507922» (prio. 1993) electrolyzes 15 wt% p-tert-butyltoluene with 0.3 wt% H₂SO₄ in methanol (≈0.81 M) in an undivided 1-mm graphite flow stack at 2–10 A dm⁻² and 4–8 F mol⁻¹, inside the 5–50 wt% claim range of the original Degner-era patent (EP 0 011 712, prio. 1978)«ep0011712» and consistent with the 15–20 wt% examples of the meta-isomer successor (US 8,629,304).«us8629304» Three conventions govern that arithmetic, each chosen because the alternative reading is plausible and wrong by a factor of two or more: a catalyst loading quoted in mol% is converted against the substrate concentration rather than read as a molarity (10 mol% at 0.05 M substrate is 5 mM, not 10 mM); a reaction scale stated in mmol is not read as a concentration (the '0.2 mmol scale' entries run at 0.03–0.17 M); and the solvent tabulated is that of the paper's optimized medium, which is not always the headline solvent (acetone, not MeOH, for waveform-controlled Kolbe; DMA, not DMF, for the kg-scale XEC; nitromethane for the radical-cation Diels–Alder; HFIP for the anodic N–N coupling). Each entry's sensitivity is linear (Eq. S1), so residual error in the eight flagged rows rescales exactly one row in proportion — none of the architecture rankings or carrier-class conclusions, which rest on order-of-magnitude contrasts, can be affected by factor-of-two revisions."),
  p("One accounting subtlety deserves an explicit flag. For mediated entries the tabulated i_lim is carried by the mediator, and two regimes must be distinguished. When the homogeneous step occurs inside the diffusion film (in-film EC′, Section S5.4), the substrate must also arrive through the same film and the total-catalysis cap F·n·D_S·C_S/δ bounds the entry. When the mediator is regenerated in the bulk instead — ex-cell mediation — the exemplar is the chloride-mediated alkene epoxidation of Leow et al.:«leow2020» their headline runs oxidize 1.0 M KCl at 300 mA cm⁻² with ethylene sparged into the anolyte, they fix the chloride optimum at 2.0 M on plant-gate cost, and propylene epoxidizes under the same conditions. The system solved here takes that optimum, "
     + EX.inputs.C_Cl_M.toFixed(0) + " M Cl⁻ oxidized at the anode with chlor-alkali physics, and propylene, whose aqueous solubility (C_sat = " + EX.inputs.C_P_mM.toFixed(1) + " mM at 1 atm, Table S7e) makes it the sparingly soluble partner that reacts with Cl₂/HOCl predominantly in the sparged bulk; every input is the registry value (Table S7d, S7e). We verified this partitioning explicitly with the NPP + EC′ solver (mediator generation at the electrode boundary condition, substrate consumption through the homogeneous source term R = k·c_ox·c_S in the film): with k = " + EX.k_M.toFixed(0) + " M⁻¹ s⁻¹ the reaction layer x_k = " + EX.x_k_um.toFixed(0) + " μm is comparable to the film itself (δ = " + EX.delta_um.toFixed(0) + " μm), so the partitioning is settled by the solve rather than by that comparison. At a representative operating point of one third of the carrier limit derived below, " + EX.i_op_mAcm2.toFixed(0) + " mA cm⁻², only " + EX.infilm_pct.toFixed(1) + "% of the generated oxidant (" + EX.i_infilm_mAcm2.toFixed(1) + " mA cm⁻² equivalent — several times the planar-profile propylene diffusion cap, " + EX.i_cap_P_mAcm2.toFixed(2) + " mA cm⁻², the excess reflecting the curved profile inside the reaction zone) reacts within the film; " + EX.exported_pct.toFixed(1) + "% is exported. The split is insensitive to the film: on a " + EX.half_delta_um.toFixed(0) + " μm film at the same current it is " + EX.infilm_pct_half_delta.toFixed(1) + "% in-film and " + EX.exported_pct_half_delta.toFixed(1) + "% exported. The solver also resolves two features the analytic bounds miss: a propylene-free, Cl₂-rich zone extending ≈" + (Math.round(EX.propylene_free_zone_um / 10) * 10).toFixed(0) + " μm from the electrode — " + (EX.propylene_free_zone_um / EX.delta_um > 0.6 ? "well over half" : "about half") + " of the film, carrying " + EX.c_OX_at_op_M.toFixed(1) + " M of lumped Cl₂/HOCl with no alkene to consume it, which is an over-chlorination selectivity risk — and a carrier limit lifted by migration. For this binary electrolyte the analytic limit is twice the Fick bound, since D_salt/(1 − t₋) = 2 D₋ identically: 2 × " + EX.i_fick_Cl_mAcm2.toFixed(0) + " = " + EX.i_analytic_mAcm2.toFixed(0) + " mA cm⁻² at δ = " + EX.delta_um.toFixed(0) + " μm, the factor of 2 for an anion oxidized in its own salt being one of the closed-form limits of §S5.6. The solver reproduces that factor through the EC′ path itself, returning " + EX.reachable_ratio_to_fick.toFixed(3) + " × the Fick bound on a " + EX.reachable_film_um.toFixed(0) + " μm film where the branch can be walked to the collapse criterion"
     + (EX.dcont.every(d => d.converged)
        ? " and, continuing that converged state outward in δ, on " + EX.dcont.map(d => d.delta_um.toFixed(0)).join(", ").replace(/, ([^,]*)$/, " and $1") + " μm films alike (" + EX.dcont.map(d => d.ratio_fick.toFixed(3)).join(", ").replace(/, ([^,]*)$/, " and $1") + " × Fick), so the carrier limit is the solved limit at the production film. Reaching it on the thick films needed one numerical care, stated in §S5.2: the oxidant is a trace in the bulk and molar at the electrode, and each species' conservation residual is scaled by its largest in-film concentration. The state that carries the limit holds " + EX.c_OX_at_limit_M.toFixed(1) + " M of lumped Cl₂/HOCl (2 D_Cl C_Cl/D_OX, independent of δ). A chlorine electrolyte cannot hold molar dissolved chlorine — it leaves the electrode as gas — and this model carries no solubility ceiling and no Cl₃⁻ speciation, the same declared gap as for Br₂ in §S5.5; the carrier limit is a property of the transport equations, reproduced here by the solver and by the closed-form identity, not a statement about the surface composition of a real chlorine anode. "
        : ". Continuing that converged state outward in δ, the branch " + (EX.dcont[0].converged ? "reaches the limit again on a " + EX.dcont[0].delta_um.toFixed(0) + " μm film (" + EX.dcont[0].ratio_fick.toFixed(3) + " × Fick)" : "does not reach the limit even on a " + EX.dcont[0].delta_um.toFixed(0) + " μm film") + " but ends before the carrier is depleted on thicker films — at " + EX.dcont[1].pct_of_analytic.toFixed(0) + "% of the analytic limit on " + EX.dcont[1].delta_um.toFixed(0) + " μm and " + EX.dcont[2].pct_of_analytic.toFixed(0) + "% on " + EX.dcont[2].delta_um.toFixed(0) + " μm. We have not established why. The state that carries the carrier limit holds " + EX.c_OX_at_limit_M.toFixed(1) + " M of lumped Cl₂/HOCl on every film (2 D_Cl C_Cl/D_OX, independent of δ), outside what a lumped, fully dissolved species can represent — a chlorine electrolyte cannot hold molar dissolved chlorine, which leaves the electrode as gas, and this model carries no solubility ceiling and no Cl₃⁻ speciation, the same declared gap as for Br₂ in §S5.5. The limit is therefore taken from the analytic identity, which requires no such state, and the concentration-controlled solve at " + EX.delta_um.toFixed(0) + " μm is reported as the lower bound it is. ")
     + "The electrode current density is carrier-limited either way (the Fick bound alone is " + EX.i_fick_Cl_mAcm2.toFixed(0) + " mA cm⁻² at this film), and the binding constraint moves to a different unit operation: gas–liquid substrate delivery (k_L·a) must be sized to match the chlorine-generation current, exactly as in the industrial chlorohydrin process. This decoupling of substrate delivery from the inter-electrode gap is the same principle exploited by the Tier-4 architectures of Section 3 (liquid diffusion electrodes; aqueous/non-aqueous soft interfaces)."),
  cap("Table S2 (following pages, landscape). The 50-reaction set with carrier assignments, carrier charge, estimated diffusivities and provenance, concentrations, electron counts, solvent, and electrolyte. z is the charge of the carrier as it reaches the electrode, read from each exemplar paper; it is the switch on the migration term, so a charged carrier in its own salt is lifted above its Fick bound and a neutral one is not. " + numWordCap(CC_MEDIUM.length) + " rows, marked *, carry a medium-confidence charge (" + CC_MEDIUM.map(k => k.replace(/ \(.*$/, "")).join("; ") + " — metal complexes whose electroactive species is written neutral); re-solving each at every alternative charge in {" + ZS.alternatives.join(", ") + "} moves its ceilings by at most " + ZS.worst_ceiling_change_pct.toFixed(1) + "% and no threshold count in any architecture (Table S7d). The bracketed number opening each C-provenance cell is the exemplar's entry in the reference list; the page/procedure anchor that follows is the location within that source from which the concentrations were computed."),
];

// Reference key(s) for each of the 50 rows, in row order (row 3 cites the Shono protocol and its modern
// Merck exemplar; row 30 cites the three BASF patents). Rendered as a plain [n] prefix on the C-provenance cell.
const ROWKEYS = [
  "kawamata2019", "liu2025", "shono1975,deprez2021", "zhao2021", "fu2017", "malviya2023", "morofuji2013",
  "zhangxu2018", "cai2021", "zhangye2022", "gnaim2022", "hioki2023", "kelly2026", "zhangbaran2022",
  "kirste2012", "mo2020", "liwilden2020", "qiu2018", "cai2022", "courtois1997", "osa1994",
  "baizer1964", "peters2019", "kisukuri2024", "kawamata2021", "yang2023nc", "ke2019", "lopezruiz2018",
  "zhong2021", "us5507922,ep0011712,us8629304", "shono1975", "leow2020", "ruecker2024", "bottecchia2022", "horn2016",
  "chien2025", "cardiel2019", "okada2016", "miller1992", "walecka2022", "gnaim2022", "bao2022",
  "ozaki1994", "zhangzeng2018", "tajima2002", "zhangqiu2025", "mei2019", "gitkis2010", "long2021",
  "gieshoff2016"
];
if (ROWKEYS.length !== rxRows.length) throw new Error("ROWKEYS length " + ROWKEYS.length + " != rows " + rxRows.length);
const rxRowsCited = rxRows.map((row, i) => { const r2 = row.slice(); r2[12] = "[⟦" + ROWKEYS[i] + "⟧] " + r2[12]; return r2; });   // C provenance is column 12 since the z column
const tableS2 = [
  mkTable(["#","Class","Reaction","Carrier","Carrier species","z","D (cm²/s)","C (M)","n_c","Solvent","Electrolyte","D provenance","C provenance"],
    rxRowsCited, [400,900,2400,800,1350,350,900,600,400,900,1500,2100,2340], 14040),
];

// ---------- S9: complete parameter provenance (registry loaded at the top of this file) ----------
const s9 = [
  h1("S9. Parameter provenance"),
  h2("S9.0 Equations for derived parameters"),
  p("Each row of Table S7 carries an Equation column naming the equation that produced it. A row "
    + "with no entry there is either a measured value, which needs no derivation, or an assumption, "
    + "which has none — and that is precisely the distinction the column exists to make visible. "
    + "The equations are collected here so that a reader can go from any tabulated number to the "
    + "arithmetic and the inputs that made it, without reading the source code."),
  eqn([{m:[msub("V","A"), mr("="), mr("Σ "), msub("n","i"), msub("v","i"), mr(" + Σ Δ"), msub("V","ring")]}], "S23", "[cm³ mol⁻¹]"),
  p("Le Bas additive molar volume, the V_A of Eq. S2. Increments v_i and the ring corrections are "
    + "tabulated per element (Table S7c) and cited individually. The assembly is checked: computed "
    + "volumes for ten reference compounds reproduce the published Le Bas values to within 1.7% "
    + "(benzene, toluene, methanol, ethanol, acetone, acetic acid, naphthalene and n-hexane exactly), "
    + "and perturbing any increment fires the check."),
  eqn([{m:[mr("D"), mr("="), mfr([msub("k","B"), mr("T")], [mr("6πμ"), msub("r","h")])]}], "S24", "[cm² s⁻¹]"),
  p("Stokes–Einstein, used for the eleven dilute molecular-catalyst carriers, for which Eq. S2 is "
    + "unavailable: Le Bas has no transition-metal increment. The hydrodynamic radius r_h = 4–5 Å is "
    + "an assumption and is the most exposed input in the diffusivity column. Inverting this equation "
    + "on the measured D of ferrocene in MeCN (2.4 × 10⁻⁵ cm² s⁻¹) gives r_h = 2.65 Å for a neutral "
    + "metallocene of MW 186; scaling as M^(1/3) to the 325–570 range of these complexes predicts "
    + "3.2–3.7 Å, so the adopted 4–5 Å is larger than expected and the resulting D is, if anything, "
    + "understated. " + cdSentence()),
  eqn([{m:[mr("D"), mr("="), mfr([msup("λ","0"), mr("RT")], [msup("z","2"), msup("F","2")])]}], "S25", "[cm² s⁻¹]"),
  p("Nernst–Einstein, used for the five small-ion carriers, for which Le Bas volumes are meaningless. "
    + "λ⁰ is taken from a limiting-conductivity table for the ion in its own solvent."),
  eqn([{m:[mr("κ"), mr("="), msub("κ","max"), msup(mrb([mfr([mr("m")],[msub("m","max")])]), "a"),
           mr(" exp"), mrb([mr("b"), msup(mrb([mr("m − "), msub("m","max")]), "2"),
           mr(" − a"), mrb([mfr([mr("m")],[msub("m","max")]), mr(" − 1")])])]}], "S26", "[mS cm⁻¹]"),
  p("Casteel–Amis. This is the only route by which any organic-solvent conductivity in this work "
    + "reaches the derived state, and it requires a measured isotherm for that exact salt and "
    + "solvent: the four fit parameters κ_max, m_max, a and b are not predictable. Dorn et al. "
    + "supply one for Bu₄NBF₄/MeCN, which is why those five rows and no others are derived."),
  eqn([{m:[mr("κ"), mr("="), mr("Λ"), mrb([mr("c")]), mr(" c")]}], "S27", "[mS cm⁻¹]"),
  eqn([{m:[msup("Λ","0"), mr(" = "), msub("ν","+"), msup(msub("λ","+"), "0"), mr(" + "),
           msub("ν","−"), msup(msub("λ","−"), "0"), mr(",     κ ≤ "), msup("Λ","0"), mr(" c")]}],
      "S28", "[S cm² mol⁻¹]"),
  p("Kohlrausch additivity and the ceiling it implies. The inequality is rigorous for any "
    + "stoichiometry — it assumes complete dissociation AND zero relaxation, and both ion pairing "
    + "and the relaxation effect can only lower κ from there. Every registered conductivity whose "
    + "ions have a λ⁰ in their own solvent was checked against it; all sit under their ceiling, at "
    + "34–72% of it. The aqueous Λ° used there are read directly from the "
    + "Vanýsek table cited under Eq. S29 (NaOH 247.7, NaCl 126.39, KHCO₃ 117.94 S cm² mol⁻¹). Only "
    + "that table's INFINITE-DILUTION column is used, which is the correct and only quantity a "
    + "ceiling needs; its finite-concentration columns are not applicable to the preparative rows "
    + "here and are not used, exactly as §S6.1 states — its NaOH row stops at 0.01 M and the table "
    + "as a whole stops at 0.1 M. The two statements are consistent: the table bounds these rows "
    + "from above, it does not supply their κ. "
    + "the per-ion values used for the non-aqueous rows are cross-checked against it by Kohlrausch's "
    + "law of independent migration — retrieved electrolyte differences reproduce per-ion differences "
    + "to better than 0.1% (λ⁰(K⁺)−λ⁰(Na⁺) = 23.40 from chlorides and 23.43 from iodides)."),
  eqn([{m:[mr("Λ"), mrb([mr("c")]), mr(" = "), msup("Λ","0"), mr(" − "),
           mrb([msub("B","1"), msup("Λ","0"), mr(" + "), msub("B","2")]), msup(mr("c"), "1∕2")]}], "S29"),
  p("The Debye–Hückel–Onsager limiting law, with B₁ = 8.204 × 10⁵/(εT)^{3/2} and B₂ = 82.5/[η(εT)^{1/2}], "
    + "so that every coefficient follows from the solvent's permittivity and viscosity alone and "
    + "nothing is transferred between salts. Both the equation and its aqueous constants are "
    + "page-anchored to Vanýsek, \u201cEquivalent Conductivity of Electrolytes in Aqueous Solution\u201d "
    + "(CRC Handbook), which prints it as Λ = Λ° − (A + BΛ°)c^{1/2} and gives A = 60.20 and B = 0.229 "
    + "for a symmetric 1:1 electrolyte in water at 25 °C; the formulas above reproduce those to 0.7% "
    + "and 0.3%. Validated on aqueous KCl from the same table: Λ° = 149.79 and Λ(0.01 M) = 141.20 "
    + "S cm² mol⁻¹, against 140.28 computed — a deviation of 0.65%. That table also states its own "
    + "validity limit verbatim, \u201creliable for c < 0.001 mol/L; with higher concentration the error "
    + "increases\u201d, which is 100–3000× below every working concentration in this work. It is reported "
    + "for scale and nothing is inferred from it here, because at every working concentration in "
    + "this work the √c term exceeds 20% of Λ⁰ and the law is outside its validity range — for two "
    + "compositions it returns a negative Λ. This is the quantitative form of the objection stated "
    + "in §S6.1: a limiting-conductivity table cannot supply κ at preparative concentration, and "
    + "only a measured isotherm can."),
  eqn([{m:[msub(mrb([mr("φM")]), "mix"), mr(" = Σ "), msub("x","j"), mrb([msub("φ","j"), msub("M","j")])]}], "S30"),
  eqn([{m:[msub("D","A"), mr(" = "), msub("D","ref"), msup(mrb([mfr([msub("V","ref")], [msub("V","A")])]), "0.6")]}], "S32", "[same solvent, same T]"),
  eqn([{m:[msub("D","A"), mrb([mr("s")]), mr(" = "), msub("D","ref"), mrb([msub("s","ref")]),
           mfr([msub("μ","ref")], [msub("μ","s")]), mfr([msub("r","ref")], [msub("r","A")]),
           mr(",     "), mfr([msub("r","ref")], [msub("r","A")]), mr(" = "),
           msup(mrb([mfr([msub("M","ref")], [msub("M","A")])]), "1∕3")]}], "S33"),
  p("Surrogate-anchored diffusivity: correct a measured D onto a structurally similar species "
    + "instead of predicting one from scratch. Eq. S32 is Eq. S2 written for two solutes in the "
    + "same solvent, so the correlation constant, the association factor, the solvent molar mass, "
    + "T and μ all cancel and only the volume ratio survives; Eq. S33 is the Stokes–Einstein "
    + "analogue, in which μ is the only solvent property that appears and a solvent change is "
    + "therefore also permitted. This matters because the weakness of Eqs. S2 and S24 is their "
    + "PREFACTOR — on the one system here where a measurement exists, Eq. S2 lands 24% low on "
    + "ferrocene in MeCN — and a ratio cancels the prefactor exactly, leaving only the assumption "
    + "that the size-dependence has the right shape between two similar solutes. Where no molar "
    + "volume is available, which is the case for every coordination complex in Table S2 because "
    + "Le Bas carries no transition-metal increment, the radius ratio is taken structurally as "
    + "M^(1/3), i.e. assuming comparable partial molar density between reference and target "
    + "(ferrocene 1.49 g cm⁻³ against 1.4–1.5 for bipyridyl and salen complexes). "
    + "**This construction is not used to overwrite the eleven catalyst diffusivities.** It gives "
    + "values 1.14–1.56× above the assumed-radius estimate, and the two bracket rather than agree: "
    + "the assumed radius is unsourced, while the anchored value inherits ferrocene's neutrality, "
    + "and the charge and stronger solvation of these complexes raise their effective radius and "
    + "push the true D back down toward it. " + (CD.conditional
      ? ("At the sourced rate constants of §S5.7 the ten-of-eleven count does depend on the choice: the deciding row sits "
         + CD.f_crit.toFixed(2) + "× short of 25 mA cm⁻² at the assigned radius and would clear it at the anchored end of the bracket, "
         + "so the count is stated as conditional on the radius (Table S7c) rather than as robust to it. ")
      : "What matters is that the conclusion does not depend on the choice — ten of eleven catalyst-carried entries clear 25 mA cm⁻² in no architecture at BOTH ends of the bracket. ")
    + "Eq. S33 is also the tool of choice for "
    + "filling a future gap: given a measured D for any structurally similar species in any "
    + "solvent, it transfers that measurement under one stated assumption rather than trusting a "
    + "correlation's absolute prefactor."),

  p("Perkins–Geankoplis mole-fraction rule for the association-factor product of a mixed solvent. "
    + "Only the product φM enters Eq. S2; the split into a nominal M and a nominal φ in Table S3 is "
    + "presentational."),
  eqn([{m:[mr("ν"), mr(" = "), mfr([mr("μ")], [mr("ρ")])]}], "S31", "[m² s⁻¹]"),
  p("Kinematic viscosity, which enters the Schmidt number of every mass-transfer correlation in "
    + "Table S1."),
  p("Table S7 groups every model parameter by category and classifies it as measured, derived, or assumed. Measured values are tied to an external source and a specific locator. Derived values are calculated by a named method from measured or derived inputs. Assumed values are used only when no suitable source is available, and each is accompanied by a sensitivity range and the conclusion it affects. If a conclusion changes within that range, the corresponding statement in this SI is qualified accordingly."),
  p("The three states admit no fourth. In particular no entry is carried as a \"lit-representative\" value — a plausible magnitude for a class of system, tolerant to a factor of about two — because such a value is not distinguishable from an invented number by a reader who cannot check it. The registry is also the only place any constant lives: the " + N_THERM_ROWS + " thermal rows carry the architecture constants rather than leaving them fixed in the code (the external film coefficient, the surface-area ratios σ, the internal film coefficients, the inter-electrode gaps, the boiling points, the cooling-band edges, the emissivity and the ambient temperature). The thermal operating point is not among them: each architecture is judged at its own median transport ceiling from the 50-reaction matrix, so no design current is declared. Two columns are new. Locator gives the page, section, table or equation, and is empty only for derived and assumption rows. Sensitivity is mandatory on every assumption row. A citation appears on a row only where it supports the value attached to it at the stated temperature and concentration; where no such source exists the row is a derived or assumption row and says so. Two large parameter families carry per-row provenance in their own tables and are referenced rather than duplicated here: the 50 carrier diffusivities, concentrations and electron counts of Table S2 (each row tagged with its estimation route and exemplar citation), and the eight homogeneous rate constants of Table S6."),
  p("Two structural findings bound the exposure that remains, and both were verified independently of the sourcing. First, κ enters only the voltage and thermal path: Eq. S1 and the Nernst–Planck and EC′ solvers use D, C, δ and z alone, so " + (CENSUS_COND.n - N_COND_CONCLUSION) + " of the " + CENSUS_COND.n + " registered conductivities " + isAre(CENSUS_COND.n - N_COND_CONCLUSION) + " display-only and " + ((CENSUS_COND.n - N_COND_CONCLUSION) === 1 ? "supports" : "support") + " no stated conclusion. Second, because the external film is " + EXT_SHARE + " of the series thermal resistance, sweeping the internal film coefficient h_int from 50 W m⁻² K⁻¹ to infinity moves every boil-off ceiling by only −5/+6%, which retires four of the new thermal rows at a stroke. What is left load-bearing, and is flagged as such in the sensitivity column, is short: δ for the stirred batch cell (Table S7g), the surface-area ratio σ of the microfluidic chip and the inter-electrode gaps of the recirculating and rotating cells, which their exemplars do not state (Table S7i), and three of the four conductivities that carry a §S6 conclusion (Table S7f). The tightest thermal margins all fall at the rotating cylinder, the architecture with the highest transport ceiling and an unchanged 2 cm ohmic path: " + f2(T_MARG("THF", "rotating cyl. 3000 rpm")) + "× for THF, " + f2(T_MARG("MeCN", "rotating cyl. 3000 rpm")) + "× for MeCN and " + f2(T_MARG("DMF", "rotating cyl. 3000 rpm")) + "× for DMF, with only the aqueous reference clearing at " + f2(T_MARG("aq. NaOH", "rotating cyl. 3000 rpm")) + "×."),
];
const letters = "abcdefghijklmnop";
pcats.forEach((cat, i) => {
  const catRows = prows.filter(r => r[pcol("category")] === cat);
  // Strings that repeat verbatim across three or more rows of a category are factored out into
  // lettered notes below the table. Nothing is lost — the machine-readable registry carries the
  // full string on every row — but it keeps a 268-row appendix legible instead of printing the
  // same 1500-character paragraph forty-five times.
  const noteLabel = new Map(); const noteText = [];
  const NOTE_LETTERS = "αβγδεζηθικλ";
  // Only `sensitivity` is factored: it is the one long column the table actually prints, so a
  // lettered note always has a referring cell. (method_note is not a column here -- see below.)
  [pcol("sensitivity")].forEach(ci => {
    const freq = new Map();
    catRows.forEach(r => { const v = (r[ci] || "").trim(); if (v.length > 120) freq.set(v, (freq.get(v) || 0) + 1); });
    // Ties are broken on the note TEXT, not left to Map insertion order. S_MU and S_RHO stood at
    // 15 occurrences each until 2026-08-30, so which of them was (α) and which (β) was decided by
    // whichever happened to be inserted first -- and giving DMA its own viscosity sensitivity
    // dropped S_MU to 14 and silently swapped both letters throughout a published table. The
    // labels are consistent either way (definition and references come from one map), but a
    // published document should not renumber its own footnotes as a side effect of an unrelated
    // edit. With a text tiebreaker the letters move only when the SET of notes changes.
    [...freq.entries()].filter(([, n]) => n >= 3)
      .sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0))
      .forEach(([v, n]) => {
        if (noteLabel.has(v)) return;
        const L = NOTE_LETTERS[noteText.length] || "*".repeat(noteText.length + 1);
        noteLabel.set(v, L); noteText.push({ L, v, n });
      });
  });
  const fold = (v) => { v = (v || "").trim(); return noteLabel.has(v) ? "see note (" + noteLabel.get(v) + ")" : v; };
  const rows = catRows.map(r => {
    const cite = (r[pcol("citation")] || "").trim();
    const loc  = (r[pcol("locator")]  || "").trim();
    return [r[pcol("parameter")], r[pcol("value")], r[pcol("units")],
            r[pcol("provenance_class")],
            (r[pcol("equation")] || "").trim() || "—",
            loc ? (cite ? cite + " — " + loc : loc) : cite,
            fold(r[pcol("sensitivity")])];
  });
  // `method_note` is deliberately NOT a column here. It is the internal working record of how
  // each value was established, written as a working note rather than as publication text. It is
  // retained in
  // data/parameters_provenance.csv and rendered for reading by data/export_method_notes.py into
  // docs/METHOD_NOTES_INTERNAL.md, both internal.
  s9.push(mkTable(["Parameter","Value","Units","State","Eq.",
                   "Citation with locator","Sensitivity / exposure"],
                  rows, [1700,900,600,900,600,3000,2300]));
  const st = { measured: 0, derived: 0, assumption: 0 };
  catRows.forEach(r => { st[r[pcol("provenance_class")]]++; });
  s9.push(cap("Table S7" + letters[i] + ". " + cat.replace(/^[0-9]+\. /, "") +
              " — " + rows.length + " entries: " + st.measured + " measured, " + st.derived +
              " derived, " + st.assumption + " assumption. Every measured entry carries a locator; " +
              "every assumption entry carries a sensitivity (§S9). Full strings for the shared " +
              "notes below are repeated on every applicable row of the machine-readable "  +
              "registry."));
  noteText.forEach(nt => s9.push(cap("(" + nt.L + ") [" + nt.n + " entries] " + nt.v)));
});

// ---- SUPPORTING FIGURES -------------------------------------------------------------------
// The SI referred to lettered figures 47 times -- §S6 alone 37 times, with panel-level
// detail -- and embedded NONE of them: word/media was empty in every build. A reader of S6 had
// 37 pointers to a figure that was not in the document. The renders existed on disk the whole
// time; nothing carried them into the .docx.
//
// They are collected here rather than interleaved because their intended inline positions are
// not recorded anywhere, and putting a figure in the wrong place is worse than collecting it.
// Supporting figures were removed on 2026-09-14 (author: "remove all the figures from the SI,
// we don't need them. This is a review/perspective."). Every lettered-figure reference in the
// prose and in the registry was re-pointed to the section that carries the analysis.


const back = [
  h1("S5. Stage 1: Nernst–Planck film model"),
  h2("S5.1 Formulation"),
  p("Within the film 0 ≤ x ≤ δ we solve, at steady state in dilute-solution theory, one conservation equation per species. The molar flux of species j is the Nernst–Planck expression (diffusion + migration; convection enters only through the film thickness δ that the reactor correlations set):"),
  eqn([{m:[msub("N","j"), mr("="), mr("−"), msub("D","j"), mfr([mr("d"), msub("c","j")], [mr("dx")]), mr("−"), msub("z","j"), mfr([mr("F")], [mr("RT")]), msub("D","j"), msub("c","j"), mfr([mr("dφ")], [mr("dx")])]}], "S3"),
  p("Conservation of mass for every species j, with the homogeneous EC′ source, is"),
  eqn([{m:[mfr([mr("d"), msub("N","j")], [mr("dx")]), mr("="), msub("ν","j"), mr("R"), mrb([mr("x")])]}, {t:",    j = 1, …, n"}], "S4"),
  p("where the single homogeneous step has the bimolecular rate law"),
  eqn([{m:[mr("R"), mr("="), mr("k"), msub("c","ox"), mrb([mr("x")]), msub("c","S"), mrb([mr("x")])]}], "S5"),
  p("with stoichiometric coefficients ν_ox = −1, ν_red = +1, ν_S = −1/(n_S·s_ox), and the proton/hydroxide partner of each system (Table S6) chosen so that the step conserves charge, Σ_j z_j ν_j = 0. Direct (non-mediated) electrolyses are the special case R = 0. The potential is closed by local electroneutrality, which replaces the Poisson equation at film scales vastly exceeding the Debye length:"),
  eqn([{m:[msum([msub("z","j"), msub("c","j"), mrb([mr("x")])], "j"), mr("="), mr("0")]}], "S6"),
  p("Conservation of charge is not imposed separately — it is a theorem of Eqs. S4–S6. Defining the ionic current density"),
  eqn([{m:[mr("i"), mrb([mr("x")]), mr("="), mr("F"), msum([msub("z","j"), msub("N","j"), mrb([mr("x")])], "j")]}, {t:",     "}, {m:[mfr([mr("di")], [mr("dx")]), mr("="), mr("F"), msum([msub("z","j"), msub("ν","j"), mr("R")], "j"), mr("="), mr("0")]}], "S7"),
  p("so the current entering at the electrode leaves the bulk face unchanged; this discrete statement is verified to machine precision (max face deviation 3×10⁻¹², §S5.6). Total mediator is likewise conserved: d(N_red + N_ox)/dx = (ν_red + ν_ox)R = 0. Boundary conditions:"),
  eqn([{m:[msub("N","j"), mrb([mr("0")]), mr("="), mfr([msub("s","j"), msub("i","app")], [mr("F")])]}, {t:"  with  "}, {m:[msum([msub("z","j"), msub("s","j")], "j"), mr("="), mr("1")]}, {t:";    "}, {m:[msub("c","j"), mrb([mr("δ")]), mr("="), msup(msub("c","j"), "bulk")]}, {t:",   "}, {m:[mr("φ"), mrb([mr("δ")]), mr("="), mr("0")]}], "S8"),
  p("the first being the galvanostatic electrode condition with electron-normalized stoichiometries (e.g., anodic oxidation of a neutral substrate releasing protons has s_S = −1/n and s_H+ = +1; a Kolbe carboxylate has s_S = −1 with z_S = −1; the 2 e⁻ quinone couple has s_red = −1/2, s_ox = +1/2, s_H+ = +1), and the second the Dirichlet bulk edge with the potential reference. The bulk Dirichlet condition on the oxidized mediator (its trace bulk value) is the perfect-sink idealization of a well-mixed reservoir; §S4 discusses when that idealization matters (ex-cell mediation)."),
  h2("S5.2 Numerics"),
  p("The film is discretized in N finite volumes (N = 80 for the Stage-1 verification cases (the §S5.3 support-ratio sweep ran at N = 60), N = 90 for EC′, on a geometric mesh whose first cell is matched to the reaction layer, dx₁ ≈ x_k/50 bounded by the uniform spacing; mesh-independence is demonstrated in §S5.6). The flux on the face between cells i and i+1 uses center-to-center spacing Δx_{i+½} and the arithmetic-mean concentration in the migration term:"),
  eqn([{m:[msub("N","j,i+1∕2"), mr("="), mr("−"), msub("D","j"), mfr([msub("c","j,i+1"), mr("−"), msub("c","j,i")], [mr("Δ"), msub("x","i+1∕2")]), mr("−"), msub("z","j"), mfr([mr("F")], [mr("RT")]), msub("D","j"), mfr([msub("c","j,i"), mr("+"), msub("c","j,i+1")], [mr("2")]), mfr([msub("φ","i+1"), mr("−"), msub("φ","i")], [mr("Δ"), msub("x","i+1∕2")])]}], "S9"),
  p("and the discrete statement of Eq. S4 integrated over cell i of width Δx_i is the flux balance actually solved,"),
  eqn([{m:[msub("N","j,i−1∕2"), mr("−"), msub("N","j,i+1∕2"), mr("+"), msub("ν","j"), mr("k"), msub("c","ox,i"), msub("c","S,i"), mr("Δ"), msub("x","i"), mr("="), mr("0")]}], "S10"),
  p("with the electrode face flux replaced by the boundary condition of Eq. S8 in the first cell and a bulk ghost value at half-spacing beyond the last cell. The unknowns are the logarithms of the nodal concentrations, u_j,i = ln c_j,i — enforcing positivity by construction — plus the nodal potentials, exactly as in the catalyst-layer model from which this solver derives.«bui2022» One residual row per species per cell is Eq. S10, row-scaled by D_j·max(C_j,bulk, 0.01·C_max, max_x c_j)/δ, and one row per cell is Eq. S7 (scaled by C_max). The last term in the row scale is the species' largest concentration in the current iterate. It is included so that an electrogenerated species that is a trace in the bulk but molar at the electrode is held to the same relative tolerance as the others: the oxidant of the chloride system is seeded at " + Number(EX.inputs.c_OX_bulk_molm3.toPrecision(2)) + " mol m⁻³ in the bulk (" + sciD(EX.inputs.c_OX_bulk_molm3 / (EX.inputs.C_Cl_M * 1000)) + " of the chloride concentration, the trace seed of Table S7e) and reaches " + EX.c_OX_at_limit_M.toFixed(1) + " M at its carrier limit. Scaled by its bulk value alone, its residual row is normalised by a reference flux " + sciD(EX.c_OX_at_limit_M * 1000 / EX.inputs.c_OX_bulk_molm3) + " times smaller than its in-film concentration implies, so the 10⁻⁹ tolerance asks for a relative accuracy of " + sciD(1e-9 / (EX.c_OX_at_limit_M * 1000 / EX.inputs.c_OX_bulk_molm3)) + " on the terms actually present; that is at the floating-point floor on thick films, and the concentration-control walk stops on a branch that exists. Table S7k gives the size of that effect. The nonlinear system F(u) = 0 is solved by damped Newton iteration,"),
  eqn([{m:[mr("J"), mr("Δu"), mr("="), mr("−"), mr("F"), mrb([mr("u")])]}, {t:",    "}, {m:[mr("u"), mr("←"), mr("u"), mr("+"), mr("λ"), mr("Δu")]}, {t:",    "}, {m:[mr("λ"), mr("∈"), mr("(0, 1]")]}], "S11"),
  p("with a dense forward-difference Jacobian, a log-step clamp (|Δu|∞ ≤ 2–3) to suppress nullspace amplification of the concentration block, backtracking line search on ‖F‖∞, and a Levenberg–Marquardt fallback (JᵀJ + 10⁻¹⁰I) on singular Jacobians. Galvanostatic operation is imposed through the boundary stoichiometry. The applied current is ramped with warm starts (natural continuation) only far enough to obtain a safe state, because that parameterisation has a fold at the limiting current and cannot cross it; the limiting current itself is then obtained by concentration control, prescribing the electroactive species' surface concentration and solving for the current, which reaches the collapse criterion c_red(0)/C_red < 10⁻³ instead of stalling short of it (§S5.5)."),
  h2("S5.3 Supporting-electrolyte limits"),
  p("Two analytic limits constrain the implementation. With a neutral substrate under a fifty-fold excess of supporting electrolyte the computed plateau reproduces Eq. S1 to 0.1% (i_lim/i_Fick = 1.000). With an anionic substrate in a binary electrolyte and no added support, the computed plateau reproduces Newman's classical migration result«newman» i_lim = 2FDC/δ exactly (2.000 computed; the factor 2 is independent of the counter-ion diffusivity). Between these limits the migration enhancement decays from 2.00 through 1.38, 1.18, and 1.04 at support ratios of 0.25, 1, and 5, and the film potential drop collapses from ~57 mV to ~1 mV. For neutral substrates the Stage 0 numbers are accurate to within a few percent at any support ratio, so Table S5 stands as computed."),

  h2("S5.4 EC′ reaction–diffusion model for mediated electrolysis"),
  p("Treating a mediator as a species that merely commutes across the film understates its ceiling whenever the homogeneous step is fast. We therefore extend the film model to the full EC′ problem: the electrode exchanges electrons only with the mediator couple (s_red = −1, s_ox = +1), the substrate carries no electrode flux, and the bimolecular source of Eq. S5 (consuming Med_ox and S, regenerating Med_red) enters every finite-volume balance (Eq. S10). The analytic reference quantities used throughout are the reaction-layer thickness, the commuting (shuttle) bound, the Savéant catalytic current,«saveant» and the total-catalysis cap:"),
  eqn([{m:[msub("x","k"), mr("="), msq([mfr([msub("D","ox")], [mr("k"), msub("C","S")])])]}], "S12"),
  eqn([{m:[msub("i","shuttle"), mr("="), mfr([mr("F"), msub("D","red"), msub("C","med")], [mr("|"), msub("s","red"), mr("|"), mr("δ")])]}], "S13"),
  eqn([{m:[msub("i","Savéant"), mr("="), msub("n","c"), mr("F"), msub("C","med"), msq([msub("D","ox"), mr("k"), msub("C","S")])]}], "S14"),
  eqn([{m:[msub("i","cap"), mr("="), mfr([msub("n","S"), mr("F"), msub("D","S"), msub("C","S")], [mr("δ")])]}], "S15"),
  p("valid in the regimes δ/x_k ≪ 1, 1 ≪ δ/x_k ≪ γ, and δ/x_k ≫ γ respectively, where γ = D_S C_S / (D_med C_med) is the substrate/mediator transport ratio. At finite amplification the Savéant expression overpredicts because the reaction layer sees partially depleted substrate; the first-order correction, which is verified to ~1%, is"),
  eqn([{m:[mr("i"), mr("="), msub("i","Savéant"), msq([mr("1"), mr("−"), mfr([mr("A")], [mr("γ")])])]}, {t:",    "}, {m:[mr("A"), mr("="), mfr([mr("i"), mr("δ")], [mr("F"), msub("D","med"), msub("C","med")])]}], "S16"),
  p("Both diffusivities in those two groups are declared constants for the base case of §S5.4 (Table S7, category 4: "
     + "D_med = " + EP.base.D_med.toExponential(0) + " and D_S = " + EP.base.D_S.toExponential(0)
     + " m² s⁻¹), so the regime boundaries of that base case inherit the "
     + "choice and we state what it costs. Setting δ/x_k = 1 and δ/x_k = γ gives "
     + "the two crossing rate constants k₁ = D_ox/(C_Sδ²) and "
     + "k₂ = γ²k₁, so the boundaries do not move "
     + "together: the shuttle/kinetic boundary scales as the mediator diffusivity and is independent of D_S, while "
     + "the kinetic/total-catalysis boundary scales as D_S²/D_med and is the more exposed of "
     + "the two. Over ±" + Math.round(100 * EP.band) + "% on both diffusivities — the "
     + "working property error of §S3.1 — the base case's boundaries move by at most "
     + EP.base.worst_span_decades.toFixed(2) + " decades in k, while the three rate constants of §S5.4 (k = "
     + EP.base.figH_k.map(function (k) { return k >= 100 ? "10" + String(Math.round(Math.log10(k))).replace(/\d/g, function (c) { return "⁰¹²³⁴⁵⁶⁷⁸⁹"[+c]; }) : String(k); }).join(", ")
     + " M⁻¹ s⁻¹) sit " + EP.base.figH_margin_decades.map(function (m) { return m.toFixed(2); }).join(", ")
     + " decades from the nearest boundary"
     + (function () {
         var inside = EP.base.figH_k.filter(function (k, i) { return EP.base.figH_margin_decades[i] < EP.base.worst_span_decades; });
         if (inside.length === 0) return ", so the regime each of those panels illustrates survives the declared values. ";
         return ": the k = " + inside.map(function (k) { return k >= 100 ? "10" + String(Math.round(Math.log10(k))).replace(/\d/g, function (c) { return "⁰¹²³⁴⁵⁶⁷⁸⁹"[+c]; }) : String(k); }).join(" and ")
           + " panel" + (inside.length > 1 ? "s sit" : " sits") + " inside that movement and illustrate" + (inside.length > 1 ? "" : "s")
           + " the kinetic regime at the declared values only, the other" + (inside.length > 1 ? "" : "s") + " survive" + (inside.length > 1 ? "s" : "") + " them. ";
       })()
     + "The three rows drawn in main-text Fig. 6d–f — " + ["Hofmann", "ACT", "NHPI"].map(function (s) {
         var r = EP.rows[s]; return (s === "Hofmann" ? "the bromide-mediated Hofmann rearrangement" : s === "ACT" ? "ACT-mediated alcohol oxidation" : "NHPI-mediated allylic C–H oxidation")
           + " (k = " + (r.k_M >= 100 ? "10" + String(Math.round(Math.log10(r.k_M))).replace(/\d/g, function (c) { return "⁰¹²³⁴⁵⁶⁷⁸⁹"[+c]; }) : String(r.k_M))
           + " M⁻¹ s⁻¹, " + r.regime_solved + ")"; }).join(", ")
     + " on the " + EP.rows.ACT.delta_um.toFixed(1) + " µm ANEC film — carry their own diffusivities (Table S6) and reach i_lim = "
     + ["Hofmann", "ACT", "NHPI"].map(function (s) { var v = EP.rows[s].ilim_mAcm2; return v >= 100 ? v.toFixed(0) : v.toFixed(1); }).join(", ").replace(/, ([^,]*)$/, " and $1")
     + " mA cm⁻², with " + ["Hofmann", "ACT", "NHPI"].map(function (s) { return (100 * EP.rows[s].share_in_film).toFixed(0) + " %"; }).join(", ").replace(/, ([^,]*)$/, " and $1")
     + " of the activated mediator consumed inside the film; their regime labels are assigned from the "
     + "solve rather than from these inequalities: substrate-limited when the substrate is exhausted at the wall, mediator-limited when "
     + "most of the activated mediator leaves the film unreacted, kinetic otherwise. Each label agrees with the analytic assignment, and "
     + "re-solving every row with D_med and D_S scaled in turn by " + (1 - EP.band).toFixed(2) + " and " + (1 + EP.band).toFixed(2)
     + (EP.labels_survive ? " leaves all three labels unchanged" : (function () {
         throw new Error("G-ECPANEL: a Fig. 6d-f regime label moves under the diffusivity band; rewrite this sentence, do not print it"); })())
     + "; the rate constants sit " + ["Hofmann", "ACT", "NHPI"].map(function (s) { return EP.rows[s].margin_decades.toFixed(2); }).join(", ")
     + " decades from their nearest analytic boundary, which itself moves by up to " + EP.rows_worst_span_decades.toFixed(2)
     + " decades across the band — the reason the labels are re-solved rather than read off the inequalities."
     + ""),
  p("Because x_k shrinks to sub-micrometer scale at large k, the film is discretized on a geometric mesh with the first cell matched to x_k as described in §S5.2."),
  p("The solver reproduces the three analytic regimes. As k → 0 the plateau recovers the commuting bound F·D_med·C_med/δ to 2.5%. At intermediate k the computed plateau tracks the Savéant catalytic current F·C_med·(D_med·k·C_S)^1/2 with the correct half-order slope, reaching a thirty-six-fold amplification over the commuting bound at k = 10³ M⁻¹ s⁻¹ for the base case (20 mM mediator, 0.5 M substrate, δ = 100 μm, D_med = 6 × 10⁻¹⁰ m² s⁻¹, D_S = 1 × 10⁻⁹ m² s⁻¹; the two diffusivities are declared constants with no source, registered as assumptions in Table S7d, and the substrate cap F·D_S·C_S/δ = 48.24 mA cm⁻² and the commuting bound F·D_med·C_med/δ = 1.16 mA cm⁻² follow from them, as does γ = D_S·C_S/(D_med·C_med) = 41.67). At larger k still, the system enters total catalysis: the substrate is exhausted inside the film, the reaction zone detaches from the wall, and the plateau saturates at F·D_S·C_S/δ — numerically identical to the ceiling the same substrate would have in a direct electrolysis. Detecting this regime correctly requires the plateau criterion to watch the electroactive species (Med_red starvation at the electrode), not the substrate, whose surface collapse is a feature of the regime rather than its end. Beyond x_k ≈ 1 μm⁻¹-scale kinetics (k ≳ 3×10³ M⁻¹ s⁻¹ here) the steady state develops a stiff moving reaction front in mid-film that our damped-Newton/dense-Jacobian scheme does not chase; in that regime the exact total-catalysis limit is reported instead (§S5.4), and porting the Levenberg–Marquardt solver of the parent CO2R code is the identified upgrade path. The regime assignments this base case supports are stated as regime statements and not as scale-invariant ones. Sweeping each diffusivity over ×1/3 to ×3 leaves the k → 0 shuttle result unchanged — the plateau recovers the commuting bound to within 1–8% in every case, and is exactly independent of D_S — but the regime that any fixed k occupies does move, because x_k ∝ √D_med and γ ∝ D_S/D_med: at k = 10³ M⁻¹ s⁻¹ a threefold larger D_S carries the system out of total catalysis and back into the Savéant regime. What is invariant is the existence and ordering of the three regimes and their selection by δ/x_k and γ, which is what §S5.4 and the corresponding main-text panels claim; each case reports the x_k, δ and inequality that certify its own label."),
  p("The design consequence sharpens the main-text argument. The mediated rows of §S6 are floors that apply when homogeneous kinetics are slow; a mediator with k ≳ 10³ M⁻¹ s⁻¹ at 0.5 M substrate erases the mediator-transport penalty entirely, making the mediated ceiling indistinguishable from the substrate-carried one while retaining the selectivity benefits of indirect electrolysis. Fast mediator kinetics thus substitute for convection inside the film — a chemical analogue of reactor engineering. The same amplification is available in principle to a dilute molecular catalyst, which is turned over at the electrode and reacts homogeneously exactly as a mediator does; the published matrix carries " + (SR ? numWordCap(SR.n_sourced).toLowerCase() : "none") + " of the eleven at their own rate constant and the other " + (SR ? numWordCap(SR.n_floor).toLowerCase() : "eleven") + " at the k = 0 floor, and §S5.7 measures what a faster cycle would buy: up to " + ckAmp.toFixed(1) + "× on the class's best-architecture ceilings, after which the dilute substrate sets the cap."),

  h2("S5.5 Mediated entries"),
  p("Every mediated entry of the 50-reaction set was re-solved with the complete EC′ treatment of §S5.4 — mediator generation at the electrode boundary condition, both mediator forms and the substrate transported through the Nernst–Planck/electroneutrality system, and consumption coupled in every film cell by the explicit homogeneous source term R = k·c_ox·c_S — across all " + ARCH.length + " reactor archetypes (" + (8 * ARCH.length) + " solves). Electron bookkeeping: electrode stoichiometries s_j are per electron (s_red = −1/n_c per mediator molecule; proton-releasing couples such as NHPI/PINO and H₂Q/BQ carry the balance of charge through an explicit H⁺ species), and the homogeneous stoichiometry consumes ν_S = −1/(n_S·s_ox) substrate per oxidant event. Homogeneous rate constants are order-of-magnitude, literature-anchored estimates (Table S6); the conclusions are regime placements through x_k = (D_ox/kC_S)^1/2 and are robust on a log scale. Every specification is checked at runtime against the model's conservation laws before any solve: Σ z_j·s_j = 1 (anodic electrode stoichiometry), Σ z_j·ν_j = 0 (the homogeneous step must conserve charge — proton- or hydroxide-coupled partners are explicit species — so that ∇·i = 0 holds across the film), and bulk electroneutrality. The collapse detector watches the electroactive reduced species only — substrate surface collapse is a feature of total catalysis and of dilute-substrate systems, not a terminal state — and the reported i_lim is reached by concentration control rather than quantized by the ramp step. The first mesh cell is matched to the reaction layer (dx1 ≈ x_k/50, bounded by the uniform spacing) per §S5.6. Ramping the current cannot cross the limiting current: dc_surf/di → −∞ there, so the Jacobian degenerates exactly at the answer and Newton fails just short of it. The ramp is therefore used only to reach a safe state, and the reported value comes from CONCENTRATION CONTROL — the reduced-mediator surface concentration is prescribed and the current solved for as an unknown, which is monotone through the fold. All " + CENSUS.n + " mediated cells reach the c_red/c_bulk = 10⁻³ collapse criterion this way: at the plateau the reduced mediator sits between " + CENSUS.lo + "% and " + CENSUS.hi + "% of its bulk value, " + CENSUS.ncoll + " of them reaching the 10⁻³ criterion exactly, " + CENSUS.n028 + " of the " + CENSUS.n + " at or below 0.28%. " + WALL_SENT + " record a Newton wall from the ramp that preceded concentration control, and their limiter carries both labels; the value published is the resolved plateau, as it is for every other cell. Doubling the mesh and refining the continuation 7.5-fold together (N = 90 → 180, growth 1.15 → 1.02) move the answer by at most 0.01% on the two rows re-solved at their production mesh . The cell that most tests this is the Hofmann system in an unstirred beaker, which has the largest δ/x_k in the set at " + Math.round(HOF_UN.delta / HOF_UN.xk) + ": the substrate is exhausted at the wall and the reaction front detaches into the interior, leaving a dead zone across which the substrate sits at 10⁻²¹ of bulk. That branch is not reachable by ramping the current up from a bulk initial state — the ramp dies far below the cell's own commuting bound of " + HOF_UN.t0.toFixed(2) + " mA cm⁻², which a homogeneous source that only regenerates the carrier cannot do, and a value under a rigorous lower bound is a dead solve rather than a conservative one. Concentration control reaches it, and resolves it at " + HOF_UN.ec.toFixed(1) + " mA cm⁻², an amplification of " + ecAmp(HOF_UN).toFixed(1) + " over that bound. This matters because " + HOF_UN.t0.toFixed(2) + " sits under the 25 mA cm⁻² threshold and would otherwise set a headline integer. The unstirred counts are therefore 12/50 and 9/50. One caveat belongs with that number: sustaining a front at x_f ≈ 150 µm requires the model to generate a few tenths of a molar Br₂ from an 0.08 M bromide bulk, fed by migration of Br⁻ into the anode — the Nernst–Planck system is satisfied exactly, but the model carries no Br₂ solubility ceiling and no Br₃⁻ speciation, so whether the chemistry supports a front that far out at 228 µm is outside what this model can answer. Every mediated cell reaches the collapse criterion, so none of them is a bound that further solver refinement could move. The practical consequence of the remaining imprecision is measured rather than argued. Replacing every solved mediated value by its closed-form envelope min(Savéant, substrate supply), and separately by its Stage-0 floor, brackets the reported counts at ≥25 mA cm⁻² between " + bracket().text + " of 50, and the architecture ordering " + ORDERING_TEXT + " is preserved at both ends. Neither endpoint is a bound: " + bracket().above + " of the " + bracket().n + " solves already sit ABOVE min(Savéant, substrate supply) — " + bracket().aboveCap + " of them above the substrate-supply term itself, because that cap assumes the reaction front sits at the electrode and the front detaches once the substrate is exhausted. It is a perturbation of comparable size, not an envelope, and not a cap. The integers in Table S5 should be read with that band; the ranking does not depend on it. The bracket is recomputed in both directions from the two matrices at build time, so this sentence cannot state a range its own model does not give."),
  mkTable(["Mediated system","k (M⁻¹s⁻¹)","k provenance (order-of-magnitude)","x_k (μm)","stirred: Stage-0 → EC′ (mA/cm²)","ANEC: Stage-0 → EC′","limiter at i_lim"],
    s6FromMatrix([["Br⁻ / Hofmann rearrangement (80 mM, MeCN)","10³","N-halogenation of amide N–H by Br₂; HOBr reactivity toward organic N–H spans amines (10⁶–10⁸) ≫ amides (≲10²–10⁴): Heeb et al.;«heeb2014» N-bromination fast relative to rearrangement: Wallis and Lane.«wallis1946» Range 10²–10⁴; aqueous-analogy estimate applied to the verified MeCN medium; direct amide kinetics sparse","2.3","21 → 335","55 → 889","≥ (Newton-wall lower bound)"],
     ["ACT / alcohol oxidation (25 mM, aq. pH 8.5)","20","oxoammonium + 1° alcohol, base-dependent 1–10²: de Nooy, Besemer and van Bekkum«denooy1996» (alkaline TEMPO⁺/alcohol kinetics); Bailey, Bobbitt and Wiberg«bailey2007» (mechanism); Badalyan and Stahl«badalyan2016» (electrochemical ACT/base co-catalysis)","7.7","1.4 → 17","6.3 → 18","mediator plateau (≥ in weak reactors)"],
     ["Cl⁻ / ethylene epoxidation (1 M KCl, aq.)","10","HOCl + simple olefins k < 1 (Li, Jiang, Manasfi and von Gunten«livongunten2020»); activated/polysubstituted alkenes 12–165 (β-ionone 12.0, α-ionone 28.1, dehydro-β-ionone 165 M⁻¹s⁻¹: Lau, Reber and Roberts,«lau2019» Table 1 p 11136 — page-verified); Cl₂/Cl₂O pathways 4–6 orders faster and dominant at high Cl⁻/low pH«livongunten2020» — but this entry is k-independent: i_lim is carrier/migration-limited and in-film consumption is ethylene-flux-capped at any k (§S4)","157","392 → 789","1145 → 2305","carrier (migration ×2.0)"],
     ["Cl₄NHPI / allylic C–H (33 mM, acetone)","0.5","PINO HAT on benzylic/allylic C–H: k = 0.1–0.7 for substituted toluenes in AcOH (Koshino, Saha and Espenson«koshino2003»); see also Nutting, Rafiee and Stahl«nutting2018» and Yang et al.«yang2023»","158","6.7 → 7.6","19 → 20","mediator (kinetics-limited)"],
     ["ACT / HMF → FDCA (40 mM, aq. pH 10)","50","oxoammonium + HMF hydroxymethyl in base, alkoxide-activated 10¹–10²: de Nooy, Besemer and van Bekkum«denooy1996» (alkaline oxoammonium/alcohol kinetics); nitroxyl-mediated HMF electro-oxidation: Vo et al.;«vo2024» Cardiel, Taitt and Choi«cardiel2019» (ACT 40 mM optimum at 100 mM HMF, pH 10 borate)","10.9","2.3 → 18","10 → 21","≥ (Newton-wall lower bound)"],
     ["BQ / Wacker–Tsuji (22 mM, MeCN/H₂O)","10²","effective BQ + Pd(0) reoxidation (coordination-then-electron-transfer; no separable bimolecular constant): Grennberg, Gogoll and Bäckvall;«grennberg1993» BQ-promoted Pd redox mechanism: Hull and Sanford.«hull2009» Effective value, crude by construction","12.7","7.6 → 28","23 → 50","≥ (Newton-wall lower bound)"],
     ["Br⁻ / electrophilic bromination (0.152 M, aq./MeCN/MeOH/DCM)","10³","Br₂ + activated arene/alkene: speciation-resolved aqueous anisole bromination (Sivey, Bickley and Victor:«sivey2015» Br₂ ≈ BrOCl < BrCl, 3–6 orders above HOBr); alkene bromination spans 10³–10⁷ (Ruasse«ruasse1993»); HOBr + olefins <0.01–10³ (Li et al.«livongunten2020»). Conservative low end 10³","3.2","50 → 111","145 → 320","substrate cap (unstirred, RDE, RCE); ≥ elsewhere"],
     ["SCN⁻ / thiocyanation (0.1 M, AcOH/HCOOH)","10²","(SCN)₂ + arene, ArH + (SCN)₂ → ArSCN + SCN⁻ + H⁺ (2 e⁻/ArH): NO direct rate measurement located — estimate by analogy to halogenation (least-constrained entry); thiocyanogen aqueous formation/hydrolysis kinetics: Nagy, Lemma and Ashby;«nagy2007» anodic thiocyanation: Gitkis and Becker«gitkis2010»","4.7","7.5 → 18","30 → 61","mediator / ≥ (mixed)"]]),
    [2200,700,3300,600,1500,1300,1500]),
  cap("Table S6. The mediated EC′ matrix (stirred batch and ANEC flow-cell columns shown; the full 8×" + ARCH.length + " matrix is solved). " + MED_SLOPE_SENT + " Stage-0 is the commuting bound F·D_med·C_med/(|s_red|·δ) — the k→0 floor; EC′ is the solver i_lim with the source term active."),
  p("The k column carries a literature pass rather than bare estimates. Where direct measurements exist (PINO hydrogen-atom transfer; HOCl + alkenes; aqueous arene bromination speciation), the adopted values sit inside the measured ranges cited in the table. Where only mechanistic anchors exist (oxoammonium/alcohol base dependence; BQ/Pd(0) coordination–electron-transfer), the value is an order-of-magnitude representative and is labeled as such. Two entries deserve explicit caution flags: the thiocyanation rate constant has no located direct measurement and is an analogy to halogenation, and the Hofmann N-bromination rate rests on the amine ≫ amide reactivity ordering of the water-treatment literature rather than an amide-specific measurement. Three statements bound the impact of these uncertainties. Two are structural: regime placement enters only as δ/x_k ∝ √k (log-scale robust), and for the chloride entry every reported conclusion — the carrier-limited i_lim at the migration ceiling of the ethylene row, and the " + EX.exported_pct.toFixed(0) + "% oxidant export of the propylene solve of §S4 — is k-independent, because in-film consumption is capped by the alkene flux, not by kinetics, at any k from the HOCl pathway (≈10) to the Cl₂ pathway (≈10⁷). The third is measured rather than argued: perturbing each rate constant by a factor of ten in either direction, one row at a time, and re-solving the mediated matrix moves at least one cell across the 25 mA cm⁻² threshold on " + KS.summary.rows_crossing_25.length + " of the eight rows — " + ksList() + " — so the ≥25 mA cm⁻² count of any single architecture moves by at most ±" + KS.summary.max_count_delta_25 + " and the ≥50 mA cm⁻² count by at most ±" + KS.summary.max_count_delta_50 + " from any one rate constant, " + (KS.summary.ordering_preserved ? "and no architecture ordering changes" : "and the architecture ordering changes") + ". The rate constants are therefore the softest input behind the threshold status of those rows, and the counts in the main text should be read with that ±" + KS.summary.max_count_delta_25 + " in mind."),
  p("Three structural results. First, source-term coupling only raises mediated ceilings — amplifications run " + AMP_ALL + " over the commuting floor — so the Stage-0 numbers in the main figures were conservative, and with the coupling active the stirred-beaker ≥50 mA cm⁻² count among mediated entries rises from " + ecCount("Stirred batch", 50, "t0") + "/8 to " + ecCount("Stirred batch", 50, "ec") + "/8 (≥25: " + ecCount("Stirred batch", 25, "t0") + "/8 to " + ecCount("Stirred batch", 25, "ec") + "/8). The chloride/ethylene entry converges to 2.0× its Fick bound in every reactor — the analytic binary-electrolyte migration factor emerging from the full model — and the Hofmann system at its verified scale-up conditions (80 mM Br⁻ carrying 0.4 M substrate, δ/x_k ≈ " + Math.round(HOF_ST.delta / HOF_ST.xk) + " stirred) amplifies ×" + Math.round(ecAmp(HOF_ST)) + ", the deep-Savéant kinetic regime: the mediator turns over inside a " + HOF_ST.xk.toFixed(1) + " μm reaction layer against a five-fold substrate reservoir, and the stirred beaker jumps from a " + Math.round(HOF_ST.t0) + " mA cm⁻² floor to " + Math.round(HOF_ST.ec) + " mA cm⁻². Second, the dilute-nitroxyl systems (ACT at 25 and 40 mM, the two experimentally documented flow/divided-cell campaigns) amplify strongly in batch (" + fRange(batchOf(ACT).concat(batchOf(HMF)).map(ecAmp), v => "×" + Math.round(v)) + ") yet land at nearly the same " + fRange(ACT.map(c => c.ec), v => String(Math.round(v))) + " and " + fRange(HMF.map(c => c.ec), v => String(Math.round(v))) + " mA cm⁻² in every reactor from beaker to RCE: fast kinetics substitute for convection, the reaction layer is already thinner than any achievable δ, and the remaining levers are C_med and k — the mediated plateau of the payoff map made concrete, the quantitative explanation for why flow chemistry alone did not push these systems over the barrier, and precisely why the 200-g levetiracetam campaign«zhong2021» engineered around the plateau with a 100 cm² divided flow stack at high area rather than higher current density. Third, the Cl₄NHPI system barely moves (" + fRange(NHPI.filter(c => c.reactor !== "Unstirred batch").map(ecAmp), v => "×" + v.toFixed(1)) + " outside the unstirred cell): with PINO hydrogen-atom transfer at k ≈ 0.5 M⁻¹ s⁻¹ the reaction layer (x_k ≈ " + Math.round(NHPI[0].xk) + " μm) is thicker than every engineered film, the bottleneck is homogeneous kinetics, not transport, and no reactor fixes it — the model correctly refuses to promise reactor gains where chemistry is limiting."),
  p("The same content can be read nondimensionally, and doing so removes the solvent and carrier properties from the comparison entirely. Against the reactor intensification x̂, the three carrier laws that follow from Eqs. S1 and S12–S15:"),
  eqn([{m:[mr("x̂"), mr("="), mfr([msub("δ","batch")], [mr("δ")])]}, {t:";   "}, {m:[msub("ŷ","direct"), mr("="), mr("x̂")]}, {t:";   "}, {m:[msub("ŷ","catalyst"), mr("="), mr("ε"), mr("x̂")]}, {t:";   "}, {m:[msub("ŷ","mediated"), mr("="), mfun("min", mrb([mr("x̂"), mr(","), mfun("max", mrb([mr("μ"), mr("x̂"), mr(","), mr("μ"), msup("λ","1∕2")]))]))]}], "S17"),
  p("with μ = n_c C_med D_med/(n_S C_S D_S), ε = n_c C_cat D_cat/(n C_S D_S), and λ^½ = δ_batch/x_k the batch Damköhler group; the min enforces the substrate cap (Eq. S15) and the max the commuting floor (Eq. S13). The electron stoichiometries are not optional in μ: for the ACT exemplar that fixes its value (n_c = 1 per mediator turnover, n_S = 2 per substrate) the ratio is 0.0205, and dropping n_S doubles the mediated plateau to 0.041."),

  h2("S5.6 Verification against analytic limits"),
  p("Every continuum-model configuration with a tractable analytic limiting current was compared against the solver. All sixteen checks pass. Stage-1: the Fick limit nFDC/δ for a neutral reactant in 10× supporting electrolyte is reproduced to +0.00%; the Newman binary-electrolyte migration factor of exactly 2 for an anion oxidized in its own salt to +0.50%; the linear-profile prediction c_surf/c_bulk = ½ at i = ½·i_lim to +0.63%; and mesh refinement from N = 40 to 160 moves the Fick comparison by ≤1%. Stage-2: the k→0 commuting bound F·D_red·C_med/δ is reproduced to −0.13% (mesh-independent to 0.1% between N = 90 and 130); the Newman factor of 2 through the EC′ code path to +0.26%; and the Savéant plateau at δ/x_k = 7.9 to +1.1% — after applying the first-order substrate-depletion correction i = i_sav·(1 − A/γ)^½; without it the asymptote overestimates by A/2γ (here 10%), which accounts for the raw deviation. Total catalysis at k = 10³ M⁻¹s⁻¹ is an asymptote rather than an equality, so the comparison is a bracket: the solver plateau must lie within [0.80·i_cap, i_cap + i_shuttle] and must never exceed the ceiling; it sits at 0.87·i_cap, approached monotonically from below."),
  p("These comparisons surface one genuine numerical limitation — on a hyper-stretched geometric mesh (fixed 0.03 μm first cell) the damped-Newton continuation stalled before full surface depletion in the deep-depletion migration regime of concentrated ionic mediators (1.43× the Fick bound where the analytic answer is 2.00×) — and the codebase was hardened in response rather than merely annotated. Four changes were made: (i) the residual scaling floor for trace species was tied to the dominant concentration instead of the trace bulk, which removed the ill-conditioning (the same binary comparison on the stretched mesh now converges to within 0.2% of the ceiling, retained as a documented case); (ii) the first mesh cell is matched to the reaction layer, dx1 ≈ x_k/50 bounded by the uniform spacing; (iii) the reported i_lim is obtained by concentration control, which reaches the collapse criterion rather than approaching it through the ramp's fold; (iv) the homogeneous stoichiometries were made explicitly charge-conserving (Σ z·ν = 0, with proton/hydroxide partners as species), enforced by runtime assertions together with Σ z·s = 1 and bulk electroneutrality. The discrete statement is then verified a referee would test — the ionic current F·Σ z_j·N_j evaluated at every interior face equals the applied current — and passes at machine precision (max deviation 3×10⁻¹²). The production mediated matrix (Table S6) was regenerated after these changes; the chloride/propylene entries now sit at 2.01× their Fick bounds, on the analytic migration ceiling"),

  h2("S5.7 Catalyst-carried entries"),
  p("Mechanistically a molecular catalyst is an EC′ carrier like a mediator: the electrode generates the active oxidation state and the substrate consumes it in solution, at a rate k c_active c_S, and the ceiling is the EC′ solution of §S5.4 with the same species set as the k = 0 layer plus the substrate at its reported concentration and a charge-balancing product of the homogeneous step. Credited with no turnover inside the film (k = 0) the catalyst is a shuttle — activated at the electrode, carried out through the film unreacted — and its ceiling is n_c F D_cat C_cat/δ, the carrier's own transport bound, which is the floor of the EC′ current because the homogeneous source can only add flux. That treatment is a direct electrolysis of a dilute species and can show nothing catalytic. The eight mediated rows carry a citable single-step rate constant (Table S6); the catalyst rows are multi-step cycles, and the constant the model needs is that of the first step that consumes the substrate."),
  p("For seven of the eleven rows that step has been measured, and the measured value is adopted as a declared transfer to the row's own ligand, solvent and substrate (state C, Table S7j). Four nickel rows — the kilogram-scale cross-electrophile coupling, the aryl amination, the amination with ammonia and the biaryl homocoupling — turn over by oxidative addition of an aryl bromide to Ni(I)-bipyridine. For the isolated complex [(CO₂Et-bpy)NiCl]₄ in THF at 26 °C that step is 7.1 ± 0.3 M⁻¹ s⁻¹ with bromobenzene and 3.4–56 M⁻¹ s⁻¹ across the para-substituted series (Hammett ρ = +1.1);«ting2022» the aryl-amination exemplar's own voltammetry in DMF loses the Ni(II/I) return wave at 100 mV s⁻¹ on adding 4-bromoanisole, which places the step at or above ≈10² M⁻¹ s⁻¹ in the reaction medium;«kawamata2019» and pulse radiolysis of (dtbbpy)NiBr with 4-bromobenzotrifluoride bounds it below 10⁴ M⁻¹ s⁻¹.«till2021» The adopted value is 10² M⁻¹ s⁻¹ with the measured bracket 10¹–10⁴ as its sensitivity. Two cobalt-electrocatalytic hydrogen-atom-transfer rows (hydroamination, isomerization) turn over by transfer of the hydride from Co(III)–H to the alkene; a finite-element fit to Co(salen) voltammetry with 4-tert-butylstyrene in DMF gives k_MHAT = 7 × 10² M⁻¹ s⁻¹,«boucher2023» hydride formation being rate-limiting in that study and in the stoichiometric work of Wilson and Holland,«wilson2024» and the exemplar's own kinetics are zero order in the alkene,«gnaim2022» consistent with a fast alkene step; 7 × 10² is adopted with 10²–10⁴ as its sensitivity, the alkene class (styrenes there, unactivated alkenes here) and the hydride source (silane there, cathodic protonation here) being the declared differences. The Co(salen) aza-Wacker row is bounded from above by the exemplar's own voltammetry: with the reaction's base and 10 mM substrate the Co(II)/Co(III) wave is unchanged at 100 mV s⁻¹ at room temperature,«cai2021» which puts the step below ≈4 × 10¹ M⁻¹ s⁻¹ there; 10 M⁻¹ s⁻¹ is adopted with 1–10² as its sensitivity (the synthesis runs at reflux, for which nothing is printed). The remaining four rows — the Ni(tet a) macrocycle cyclization, the manganese diazidation (an azidyl-radical step), the copper/anthraquinone photoelectrochemical cyanation (the substrate is consumed by the photoexcited quinone) and the rhodium C–H alkenylation — carry no measured constant for the step the model needs and stay at k = 0, the floor, with the declared band below as their sensitivity. The seven sourced cells are overlaid on the published matrix exactly as the mediated cells are (Table S5), and the k = 0 member of every solve reproduces the published cell to " + (SR && Math.abs(SR.control.worst_rel) < 1e-4 ? "better than 0.01" : (SR ? (100 * Math.abs(SR.control.worst_rel)).toFixed(2) : "?")) + " % — the control that the sourced layer is the same problem with the source switched on."),
  p((function () {
    var rows = [["Ni-XEC C(sp2)-C(sp3) (ArBr + RBr)", "Ni–XEC"], ["Co-H alkene reduction (e-HAT)", "cobalt hydride"], ["Co-catalyzed aza-Wacker cyclization", "aza-Wacker"]];
    var g = rows.map(function (r) { var q = srRow(r[0]); if (!q) throw new Error("S5.7: no sourced row " + r[0]); return "×" + q.gain_unstirred_to_rce.toFixed(1) + " (" + r[1] + ")"; });
    var g0 = rows.map(function (r) { return "×" + srRow(r[0]).gain_at_k0.toFixed(0); });
    return "The three rows drawn in main-text Fig. 6h gain " + g.join(", ").replace(/, ([^,]*)$/, " and $1")
      + " from the unstirred to the rotating-cylinder film at their cited rate constants, against " + g0.join(", ").replace(/, ([^,]*)$/, " and $1")
      + " for the same rows at k = 0. A transport-limited carrier gains the full 1/δ ratio; a carrier regenerated inside its own reaction layer gains only a few-fold.";
  })()),
  p("Sensitivity. All eleven rows are also re-solved over a declared band k ∈ {" + ckK.map(k => ckSci(k)).join(", ") + "} M⁻¹ s⁻¹ — the band the mediated rows carry, and one decade above it — which brackets every adopted value and supplies the floor rows' sensitivity. The substrate diffusivity is the second declared input, 1.0 × 10⁻⁹ m² s⁻¹ at the acetonitrile viscosity scaled as 1/μ to each row's solvent (Table S7d); it enters only through the substrate cap n_S F D_S C_S/δ, and the table marks the rows whose ceiling sits at that cap. The k = 0 member of every sweep reproduces the published k = 0 cell to " + (Math.abs(CK.control.worst_rel) < 1e-4 ? "better than 0.01" : (100 * Math.abs(CK.control.worst_rel)).toFixed(2)) + " % (worst of " + CK.control.cells + " cells)."),
  p("Result. " + ckSentence().replace(" (§S5.7)", "") + " " + srCountMoves() + " " + ckBandSentence() + (ckAt(ckKmax).rows_clearing25.length ? " The rows that clear 25 mA cm⁻² somewhere within the band: " + ckClearList() + "." : "") + " " + ckWalls() + " The design consequence for the main text follows directly: a catalyst-carried row with a fast homogeneous step behaves as a direct electrolysis of a dilute substrate, and its levers are the substrate concentration and the architecture; one with a slow step is capped by the catalyst loading; and in the kinetic regime between them, where the seven sourced rows sit, thinning the film buys a few-fold rather than the 1/δ of a transport-limited row."),
  mkTable(["Catalyst-carried entry", "C_cat (mM)", "C_S (M)", "k adopted (M⁻¹ s⁻¹)", "published ceiling, best of seven (mA cm⁻²)", "best at k = 0", "best at k = " + ckSci(ckKmax), "max × in band", "at substrate cap"],
    ckRows.map(([nm, r]) => { const q = srRow(nm); return [ckShort(nm), r.C_cat_M != null ? (1000 * r.C_cat_M).toFixed(1) : "", r.C_S_M != null ? r.C_S_M.toFixed(3) : "",
      q ? srK(q.k_M) : "0 (floor)", q ? q.best_mAcm2.toFixed(2) : r.i_k0_best_mAcm2.toFixed(2),
      r.i_k0_best_mAcm2.toFixed(2), r.i_ec_best_mAcm2_at_kmax.toFixed(1), r.max_amplification.toFixed(1),
      (q ? q.cells_at_substrate_cap > 0 : r.substrate_capped_at_kmax) ? "yes" : "no"]; }),
    [3.0, 0.9, 0.9, 1.3, 1.6, 1.0, 1.0, 0.9, 1.0]),
  cap("The eleven catalyst-carried rows: the adopted rate constant (§S5.7, Table S7j), the ceiling the matrix publishes at it (the largest of the seven architectures), and the declared-band sweep around it. A row is at its substrate cap when a published cell (or, for a floor row, its ceiling at k = " + ckSci(ckKmax) + ") is within 5 % of n_S F D_S C_S/δ; there the declared D_S is what sets the number."),
  h1("S6. Cell voltage and the Joule-heating ceiling"),
  p("The cell-voltage stack is"),
  eqn([{m:[msub("E","cell"), mrb([mr("i")]), mr("="), msub("E","0"), mr("+"), mr("2"), mfr([mr("2RT")], [mr("F")]), mfun("asinh", mrb([mfr([mr("i")], [mr("2"), msub("i","0")])])), mr("+"), mfr([mr("i"), mr("L")], [mr("κ")])]}], "S18"),
  p("with a representative E₀ = 2.0 V thermodynamic-plus-kinetic floor and symmetric Butler–Volmer asinh terms for the two electrodes (α = ½, i₀ = 1 mA cm⁻² per electrode; both illustrative — the ohmic term dominates every conclusion above ~10 mA cm⁻²). The Joule dissipation per electrode area is"),
  eqn([{m:[mr("Q"), mr("="), mfr([msup("i","2"), mr("L")], [mr("κ")])]}], "S19"),
  p("At 100 mA cm⁻² across the canonical 2 cm beaker gap of §S6.1, in 0.2 M NaI/DMF (κ = 8.77 mS cm⁻¹, the registered preparative electrolyte adopted for §S6), E_cell = 25.3 V, of which 22.8 V is ohmic; the same cell at 50 mA cm⁻² draws 13.8 V, which is the 10–20 V range common in academic non-aqueous reports. The overpotential heat at 100 mA cm⁻² is q = 2.3 W cm⁻². A 100 mL batch of DMF under 10 cm² of such electrode (m·c_p = 194 J K⁻¹) initially self-heats at ≈7.2 K min⁻¹, and the full lumped balance of §S6.1 places its passive steady state at T_ss ≈ " + DMFX.T_ss_C.toFixed(0) + " °C, above DMF's 153 °C boiling point. Both of those statements are conditional on the adopted κ and must be quoted with the condition, because that κ is derived rather than measured (§S9, Table S7f): Λ° = 81.35 is measured directly, and the attenuation at 0.2 M is transferred from a measurement of the same salt in methanol, which makes 8.77 a floor rather than a best estimate. T_ss falls back to the boiling point at κ = " + DMFX.kappa_Tss_at_boil_mScm.toFixed(2) + " mS cm⁻¹, a margin of " + xmul(DMF_TSS_FOLD, 2) + ", and the 13.8 V figure leaves the 10–20 V band at κ = " + DMFX.kappa_E50_10V_mScm.toFixed(2) + " mS cm⁻¹ (×" + (DMFX.kappa_E50_10V_mScm / 8.77).toFixed(2) + ") or κ = " + DMFX.kappa_E50_20V_mScm.toFixed(2) + " mS cm⁻¹ (×" + (DMFX.kappa_E50_20V_mScm / 8.77).toFixed(2) + "). Both thresholds lie inside the 4–16 mS cm⁻¹ band of that row, so both statements are conditional on the adopted κ. What the worked example supports without that qualification is the direction: at any κ in the band the cell dissipates ohmically far more than it dissipates kinetically, and the conclusion is not that it runs hot but that it approaches boiling. At the adopted κ, 100 mA cm⁻² is not passively reachable in an unstirred beaker of DMF, consistent with the " + T_CEIL("DMF", T_ARCH[0]).toFixed(0) + " mA cm⁻² passive ceiling §S6.1 reports for the same electrolyte and gap; the same experiment in 3.0 M LiBr/THF crosses THF's 66 °C boiling point in under two minutes. This is the quantitative content of the anecdotal industrial reports of solvent loss during scaled sulfoxide oxidations. The same example in 0.1 M Bu₄NBF₄/DMF — measured at κ = 4.76 mS cm⁻¹ (Table S7f) — across a 5 mm gap gives " + f2(EX_ECELL) + " V, of which " + f2(EX_OHMIC) + " V is ohmic, " + f2(EX_Q) + " W cm⁻² of heat and a passive steady state of " + EX_TSS.toFixed(0) + " °C. That is the illustration the main text carries, and it is a tighter cell than the canonical beaker archetype rather than one of the modelled architectures: at the 2 cm spacing of §S6.1, on the registered preparative electrolyte, the conclusion inverts. The remedy is geometric and architectural, not chemical: the same electrolyte in the 25 μm gap of the microfluidic archetype carries eight hundred times less ohmic heat at equal current — a thirty-fold reduction in the total heat load once the activation term is included — and the cooled bipolar-plate architectures of PEM electrolyzer stacks reject of order 0.3–2.5 W cm⁻² across in-cell gradients of 14–27 K. That figure is stated conservatively: a range of 1–10 W cm⁻² is sometimes quoted on a citation that resolves to Eichner et al., Front. Chem. Eng. 2024, 6, 1384772, which in fact reports 0.32–0.42 W cm⁻² into the anodic fluid at 2 A cm⁻² with gradients of 13.6–17.1 K, an order of magnitude below that quoted range. The thermodynamic check agrees with the lower figure: a PEM electrolyzer at 2 A cm⁻² and 1.9 V against a 1.48 V thermoneutral voltage generates 0.84 W cm⁻², and at 3 A cm⁻² and 2.1 V, 1.9 W cm⁻². The corresponding coefficient for that cooling class, U′ = 0.30 W cm⁻² K⁻¹, is not taken from that literature at all but derived from laminar internal-flow heat transfer in water channels (Nu = 4.36–8.23, D_h = 1–3 mm), which brackets it at 0.09–0.49 W cm⁻² K⁻¹ (Table S7i). Passive rejection is far weaker and is bounded by geometry rather than by any assumed cooling envelope: the construction of §S6.1 gives U′ = " + U_UNST.toFixed(4) + " W cm⁻² K⁻¹ for a 100 mL beaker in still air, rising only to " + U_STIR.toFixed(4) + " W cm⁻² K⁻¹ when the liquid is stirred. It is this coefficient, not any transport figure of merit, that bounds the current density a beaker-scale non-aqueous cell can sustain thermally."),
  h2("S6.1 Steady-state temperature and boil-off current"),
  p("To answer whether cells actually reach solvent boil-off rather than merely dissipating uncomfortable power, we close a lumped energy balance on a representative 100 mL cell with 10 cm² electrodes. The dissipated overpotential heat per electrode area, the steady state, the boil-off current, and the exact transient are"),
  eqn([{m:[mr("q"), mrb([mr("i")]), mr("="), msb([mr("2"), mfr([mr("2RT")], [mr("F")]), mfun("asinh", mrb([mfr([mr("i")], [mr("2"), msub("i","0")])])), mr("+"), mfr([mr("i"), mr("L")], [mr("κ")])]), mr("·"), mr("i")]}], "S20"),
  eqn([{m:[msub("T","ss"), mr("="), msub("T","amb"), mr("+"), mfr([mr("q"), mrb([mr("i")])], [mr("U′")])]}, {t:";     "}, {m:[mr("q"), mrb([msub("i","boil")]), mr("="), mr("U′"), mrb([msub("T","b"), mr("−"), msub("T","amb")])]}], "S21"),
  eqn([{m:[mr("T"), mrb([mr("t")]), mr("="), msub("T","amb"), mr("+"), mfr([mr("P")], [mr("UA")]), mrb([mr("1"), mr("−"), msup("e","−tUA∕C")])]}, {t:",   "}, {m:[msub("t","boil"), mr("="), mfr([mr("C")], [mr("UA")]), mfun("ln", msb([mfr([mr("P")], [mr("P"), mr("−"), mr("UA"), mr("Δ"), msub("T","b")])]))]}, {t:"   (exists only if P > UA ΔT_b)"}], "S22"),
  p("where U′ = UA/A_elec is the heat-rejection coefficient referred to electrode area, P = q·A_elec, and C = m·c_p the electrolyte heat capacity. The passive coefficient is derived from the reactor geometry. Treating the internal and external films in series and referring the result to electrode area gives U′ = [(1/h_int + 1/h_ext)⁻¹]·σ, with σ = A_external/A_electrode the ratio of heat-rejecting surface to electrode area, h_ext ≈ 13 W m⁻² K⁻¹ for natural convection plus radiation (radiation is comparable to convection at 60–150 °C and omitting it would overstate the boiling problem), and h_int ≈ 100, 800 and >2000 W m⁻² K⁻¹ for stagnant, stirred and forced-flow electrolyte respectively. For the 100 mL beaker, σ is the wetted wall plus base of a 100 mL charge in a 5 cm inside-diameter vessel (fill height 5.09 cm): A_external = 0.00996 m² over 10 cm² = 1×10⁻³ m² of electrode, so σ = " + SIG_B.toFixed(2) + " and U′ = " + U_UNST.toFixed(4) + " W cm⁻² K⁻¹. This is " + _pct(1 - U_UNST / TSUP.assumed_U) + " below the 0.02 W cm⁻² K⁻¹ still-air value often assumed, and using it lowers every passively cooled beaker ceiling by " + ASSUMED_DROP + " relative to that value. h_ext is held at its 65 °C value; at DMF's boiling point the coefficient rises to 18.2 W m⁻² K⁻¹, which would raise the DMF beaker ceiling by " + HEXT_RISE + ". The same construction exposes a consequence that a fixed cooling axis conceals: intensified cells are compact, so their σ falls (≈7 for the microfluidic chip, ≈0.8 for an interior cell of a zero-gap stack, which is enclosed by its neighbours), while the four archetypes that intensify transport without changing the cell body — the two flow cells and the two rotating electrodes — inherit the beaker's σ = " + SIG_B.toFixed(2) + " because none of their exemplars states an electrode separation or an electrode area. Neither declared value has a source; each is reproduced by a package geometry given in Table S7i, and the σ those four take from the beaker is swept there as a breaking point rather than as a band. Intensification therefore carries a heat-rejection penalty that partly offsets its heat-generation advantage, and stirring a beaker is nearly useless thermally (U′ rises only " + U_UNST.toFixed(4) + " → " + U_STIR.toFixed(4) + " W cm⁻² K⁻¹) because h_ext, not h_int, is the limiting resistance. Active thermal management is treated as a separate axis in §S6.2 rather than bundled into a geometry label."),
  p("One consequence of that series structure deserves stating explicitly, because the lumped "
     + "h_int is least defensible exactly where a reader is most likely to challenge it. At the "
     + "25 \u00b5m gap of the microfluidic archetype the thermal entry length is a substantial "
     + "fraction of the channel and "
     + "axial conduction is not obviously negligible, so a fully developed Nusselt number is not "
     + "the right basis for h_int there. Both objections are correct as physics and neither can "
     + "reach a published number, because both are corrections to h_int and h_int is the larger "
     + "of two series conductances by a factor of "
     + Math.round(HB.reactors["microfluidic 25 $\\mu$m"].h_int_over_hext) + ". Replacing it with "
     + "a perfect internal film \u2014 h_int \u2192 \u221e, which bounds every developing-flow "
     + "or entry-length correction that could ever be made \u2014 raises U\u2032 on that row by "
     + (100 * HB.reactors["microfluidic 25 $\\mu$m"].rel_change_up).toFixed(2) + "%. The "
     + "quantity that would have to be re-derived to answer the objection properly is therefore "
     + "one that cannot move a ceiling, a margin or a verdict "
     + ""),
  p("Electrolyte selection for the thermal analysis of §S6 is constrained to entries that carry provenance in the registry of Table S7f, and prefers preparative compositions whose concentration is page-anchored to a named process. Two of the four conductivities are now measured — MeCN and the aqueous reference — one is derived (DMF) and one remains an assumption (THF), and each is quoted below with the margin at which the statement it supports would flip. THF uses 3.0 M LiBr/THF, whose composition is page-anchored to the supporting information of the 100 g Birch flow process of Peters et al.«peters2019» (1.0 mol LiBr in 320 mL THF, SM p. S15) but whose conductivity, κ ≈ 3 mS cm⁻¹, is an order-of-magnitude estimate for a heavily ion-paired ether medium and not a measurement — THF has ε = 7.6 and a Bjerrum critical distance of 3.7 nm, so association is essentially complete and no limiting-conductivity route can reach it. No single margin is quoted for this row, because none holds across the §S6.1 pass/fail verdicts. Recomputed from the lumped thermal model at κ = 3.0 mS cm⁻¹ and T_b = 66 °C, and judged against each architecture's own transport ceiling, THF does not boil in the batch cells, the recirculating cell or the microfluidic chip: those verdicts would reverse only at " + THF_PASS_LO.toFixed(2) + "–" + THF_PASS_HI.toFixed(2) + "× the carried conductivity, far below it. Where THF does fall short the multipliers are " + xmul(THF_BIND[1].multiple) + " (" + ARCH_SHORT(THF_BIND[0]) + ") and " + xmul(THF_RCE) + " (rotating cylinder), and the zero-gap stack is unreachable on κ at all, its activation term alone putting out 0.71 W cm⁻² at 1000 mA cm⁻² against 0.043 W cm⁻² of passive rejection. The binding verdict is the " + ARCH_SHORT(THF_BIND[0]) + " at " + xmul(THF_BIND[1].multiple) + ", against a band whose top is 2.19× the carried value. One further THF statement in this section is tighter still: the zero-gap cooling-duty claim of §S6.2 flips at 1.30×, and it is quoted with that margin where it appears; the floor for this row is 0.256 mS cm⁻¹, which is the highest concentration at which LiBr in THF has actually been measured (Das, J. Solution Chem. 2008, 37, 947–955, Table 1: κ = 0.256 mS cm⁻¹ at 0.316 M) and which independently corroborates the state-B floor of 0.206 mS cm⁻¹ obtained from the cell resistance of Lee et al., Org. Process Res. Dev. 2022, 26, 2674–2684. Across the band the verdicts this section reports do not turn: the microfluidic chip clears at every point in it and both rotating cells and the stack fail at every point in it. What the band alone decides is the three centimetre-gap cells, which clear at the carried value and above and fall to their own transport ceilings only at the state-B floor of 0.206 mS cm⁻¹. Das's twenty points rise as κ ∝ c^n over the top decade of the measured range (n = 1.75–2.20 depending on the fitting window); continued to 3.0 M they give 10.9–35.6 mS cm⁻¹, all below the rotating-disc reversal at " + THF_BIND[1].kappa_reverse_mScm.toFixed(1) + " mS cm⁻¹. None of those continuations is physically sound. Peters' own recipe is 1.0 mol LiBr in 320 mL THF, which is **3.92 mol THF per mole of salt**; since Li⁺ in an ether is four-coordinate, the cation's solvation shell alone accounts for all of it, leaving nothing for Br⁻ or for bulk solvent — and the conclusion survives across the plausible range of coordination number, since even at n = 3 only 23% of the THF is free. Das's highest measured point, by contrast, has 39 mol THF per mole of salt. The two concentrations are not the same kind of liquid: the c^1.75 branch describes ions migrating through bulk THF, and at 3.0 M that bulk does not exist, so κ must already have passed its maximum. Cai et al. (J. Am. Chem. Soc. 2023, 145, 25716–25725), running 2 M LiBF₄ in THF, report from molecular dynamics that Li⁺ in cyclic ethers is only partially solvated and the ions form contact ion pairs and aggregates — the same solvation-starved picture. This fixes the direction but does not locate the maximum, so no upper bound on κ is established. The aqueous reference uses 1 M NaOH (κ = 174.5 mS cm⁻¹, now measured), and its CRC citation stands: the applicable table is not p. 5-74, the 25 °C equivalent-conductivity table that stops at 0.1 M, but p. 5-71 (\"Electrical Conductivity of Aqueous Solutions\", 20 °C, 0.5–50 mass %) reaches this row directly and, combined with the concentrative-properties conversion 1.000 M = 3.840 mass % and a 20 → 25 °C correction at α = 1.5–1.9%/K, derives 174–182 mS cm⁻¹.«crc» The adopted 174.5 mS cm⁻¹ is not that derivation but a measurement, read off a raw isotherm rather than reconstructed; it sits just below the lower edge of the CRC-derived band, which corroborates it. The aqueous margins are " + NAOH_RANGE + " across the preparative architectures and survive anywhere in the band. MeCN uses 0.25 M Bu₄NBF₄ (κ = 19.95 mS cm⁻¹), now measured: it is read directly off the raw isotherm in the Supporting Information of Dorn et al., J. Chem. Eng. Data 2024, 69, 1493–1502, rather than reconstructed by Casteel–Amis from the fit the article body prints in Table 3, p. 1499. That reconstruction gives 18.9 mS cm⁻¹; the two agree to 5.6%, which is the size of the error a fit-and-invert route carries here. The value is cross-checked at 1 M against Gong et al., Energy Environ. Sci. 2015, 8, 3515–3530 to +1.4%; the band is 15–23 mS cm⁻¹. A mass-action bound of 24–36 mS cm⁻¹ is not used — it is a Lee–Wheaton extrapolation some 25× above its own fitted range, and a measured isotherm outranks an extrapolated bound. DMF uses 0.2 M NaI (κ = 8.77 mS cm⁻¹), which is derived rather than measured and is the most exposed number in the registry: its binding verdict (the " + ARCH_SHORT(DMF_BIND[0]) + ") reverses at " + xmul(DMF_BIND[1].multiple, 2) + "" + (DMF_BIND_IN_BAND ? ", inside the row's own 4–16 mS cm⁻¹ band," : "") + " and the steady-state sentence of §S6 resting on it flips at " + xmul(DMF_TSS_FOLD, 2) + ". λ°(Na⁺) = 29.81 and λ°(I⁻) = 52.11 S cm² mol⁻¹ in DMF at 25 °C are page-anchored to Gopal and Jha, Indian J. Chem. 1977, 15A, 80–83, Table 2, p. 81. Kohlrausch additivity then gives Λ° = 81.35 ± 0.04 S cm² mol⁻¹ measured directly and a hard ceiling κ ≤ cΛ° = 16.27 mS cm⁻¹. Λ(c) at the working 0.2 M has never been measured for this salt in this solvent, so the row is derived rather than measured: the attenuation is taken from Dorn's measured NaI-in-methanol isotherm at the same molarity (Λ/Λ° = 0.539) and applied to Λ° = 81.35 measured directly by Krumgalz and Barthel, giving 8.77 mS cm⁻¹. That transfer is conservative in a known direction, so the value is a floor. §S6 uses preparative compositions rather than voltammetry-grade supporting electrolytes such as 0.1 M Bu₄NPF₆/THF (0.51 mS cm⁻¹ at 22.0 ± 1.0 °C; Zhang et al., JACS Au 2023, 3, 2280–2290, Table 1). That choice is not merely unrepresentative but self-invalidating: at its apparent 15 mA cm⁻² ceiling the 2 cm cell requires 52 V, of which 50 V is ohmic, so the thermal limit sits far behind a voltage limit no laboratory supply would reach. Quoting a thermal ceiling that cannot be approached without an implausible cell voltage overstates the thermal problem while understating the ohmic one. With the preparative electrolytes adopted here the two constraints converge, which is the physically meaningful statement: both are expressions of the same iL/κ term."),
  p("This section separates the variables that decide whether a cell boils, across the preparative architectures of the transport ladder of Table S5 plus the zero-gap stack as an industrial reference. Each architecture is judged against its own median limiting current from the 50-reaction matrix rather than against a declared design current, so the analysis asks one question: at the current transport allows, can the cell reject the heat? Fixing the reactor — an unstirred beaker at the canonical 2 cm spacing, 10 cm² electrodes, passive cooling — and varying only the solvent: THF (3.0 M LiBr) boils at " + T_CEIL("THF", T_ARCH[0]).toFixed(0) + ", MeCN at " + T_CEIL("MeCN", T_ARCH[0]).toFixed(0) + ", DMF at " + T_CEIL("DMF", T_ARCH[0]).toFixed(0) + " and aqueous NaOH at " + T_CEIL("aq. NaOH", T_ARCH[0]).toFixed(0) + " mA cm⁻². Every ceiling in this section is a lower bound, because κ is evaluated at 25 °C while the cell approaches its boiling point; §S6.3 brackets that omission and the numbers here are its conservative end. Taking the same ceilings across the architectures against each one's own median transport ceiling, wherever the transport ceiling sits above a solvent's boil-off ceiling the cell boils before it reaches the current transport allows. Together these results show that in the batch and thick-gap flow cells nothing boils, because transport binds long before heat does — the unstirred beaker reaches only " + T_IDES[T_ARCH[0]].toFixed(1) + " mA cm⁻² on transport grounds, where even THF has a margin of " + f2(T_MARG("THF", T_ARCH[0])) + "×. Heat becomes the binding constraint only once transport is intensified. At the two rotating archetypes, whose transport ceilings are the highest in the model at " + T_IDES["RDE 1600 rpm"].toFixed(0) + " and " + T_IDES["rotating cyl. 3000 rpm"].toFixed(0) + " mA cm⁻², all three organic solvents fall short under passive cooling (margins " + f2(T_MARG("THF", "RDE 1600 rpm")) + "–" + f2(T_MARG("DMF", "RDE 1600 rpm")) + "× at the disc and " + f2(T_MARG("THF", "rotating cyl. 3000 rpm")) + "–" + f2(T_MARG("DMF", "rotating cyl. 3000 rpm")) + "× at the cylinder), and only the aqueous reference clears. The zero-gap stack fails in all four electrolytes, by factors of " + T_SOLV.map(x => f1(T_IDES["zero-gap PEM stack"] / T_CEIL(x, "zero-gap PEM stack")) + "\u00d7 (" + T_PRETTY[x] + ")").join(", ") + ". Across the whole ladder the absolute ceiling does not rise monotonically with intensification: for DMF it runs " + T_ARCH.map(a => T_CEIL("DMF", a).toFixed(0)).join(", ") + " mA cm\u207b\u00b2, flat wherever the gap is unchanged, rising only where it is thinned, and falling again in the stack, whose enclosed geometry withdraws more rejecting surface than its 100 \u03bcm gap saves in ohmic heat. The microfluidic cell clears all four, by " + f2(T_MARG("THF", "microfluidic 25 $\\mu$m")) + "× in THF, with a transport ceiling within a few per cent of the rotating disc's. This contrast identifies the key geometric distinction. Rotating an electrode thins the diffusion layer roughly twentyfold and moves no electrode, so it buys transport and no thermal headroom at all; only the microfluidic cell thins the GAP. That is the physical statement the section rests on: the boil-off ceiling is a balance between two terms that do not scale together \u2014 the ohmic heat a cell generates, which carries the gap and the conductivity, and the temperature rise its solvent allows before boiling \u2014 and the interelectrode gap sets the balance between these terms, because the gap is the only geometric term the heat balance contains. At a centimetre gap the ohmic term carries 85 to 98 per cent of the heat and conductivity ranks the solvents; thin the gap and it collapses onto a kinetic floor that is the same for every solvent, leaving only the boiling point to rank them. Panel (c) turns that balance into the cooling duty of §S6.2. " + T_SHARED.length + " of the " + T_ARCH.length + " architectures in fact share the same 2 cm ohmic path (" + T_SHARED.join(", ") + ") and their boil-off ceilings therefore span only " + (100 * TGEO.ceiling_spread_on_shared_gap).toFixed(1) + "% while their transport ceilings span " + TGEO.transport_span_on_shared_gap.toFixed(1) + "×. Transport intensification and thermal intensification are different axes, and this is where that shows."),
  h2("S6.2 Cooling duty"),
  p("Where a cell does fall short the design question is not whether it boils but how much cooling it needs. Setting T_ss to the boiling point at the architecture's own transport ceiling inverts the balance for the required heat-rejection coefficient, U′_req = q(i_design)/(T_b − T_amb), reported in §S6.2 against the three cooling classes and against what each cell rejects unaided. \"Passive\" here means no fan, no pump and no coolant loop: heat crosses the internal film and then an external film of h_ext ≈ 13 W m⁻² K⁻¹ (natural convection plus radiation) into still air, referred to electrode area through σ. That external film is the limiting resistance throughout, which is why stirring a beaker is nearly useless thermally and why what each cell supplies unaided is set almost entirely by its own σ: " + T_U[T_ARCH[2]].toFixed(4) + " W cm⁻² K⁻¹ for the centimetre-gap cells at σ = " + T_SIGMA(T_ARCH[2]).toFixed(2) + ", " + T_U["microfluidic 25 $\\mu$m"].toFixed(4) + " for the microfluidic chip at σ = 7.0 and only " + T_U["zero-gap PEM stack"].toFixed(4) + " for an interior cell of a stack at σ = 0.8, which is enclosed by its neighbours. Where passive rejection falls short, the two rotating cells need forced air in MeCN and DMF and a liquid cold plate in THF, and the stack needs a cold plate in THF. Nothing in the organic set demands cooling beyond classes that are ordinary engineering. The practical statement is therefore narrower than \"thin gaps require active cooling\": the architectures that need active thermal management are the ones that raise the transport ceiling WITHOUT touching the gap, because they leave the heat source exactly where it was while asking the cell to run an order of magnitude harder. Because these duties are computed with κ at 25 °C they are upper bounds on the true requirement, in the same sense that the ceilings of §S6.1 are lower bounds (§S6.3)."),
  p("Four accounting choices deserve explicit statement. (i) Ohmic term: V_ohm = i·L/κ is the planar (parallel-plate, 1D primary) resistance with κ from Table S4. The beaker rows use the 2 cm spacing of ordinary laboratory practice rather than 5 mm, so the gap itself is not optimistic; that is already carried in the ceilings quoted above and must not be applied a second time. What remains optimistic is the geometry: small electrodes in a large vessel carry a primary-current-distribution factor above the planar L/κ·A, so the beaker boil-off currents are still upper bounds for typical beaker practice, by a smaller margin than the 2–4× a 5 mm gap would imply. (ii) Vessel size and thermal mass: heat capacity does not enter the steady state at all — T_ss = T_amb + q/U′ contains no C — but it does not follow that boil-off is independent of cell volume, because inventory and rejecting surface are physically coupled. Scaling a vessel scales A_external, hence σ and U′; with ohmic heat ∝ i²L/κ and A_external ∝ V^(2/3), the ceiling follows i_boil ∝ V^(1/3). For DMF at a 2 cm gap over 10 cm² electrodes the passive ceiling runs " + [50, 100, 500, 1000].map(v => THERM.volume_sweep.i_boil_mAcm2.DMF[String(v)].toFixed(0)).join(", ").replace(/, ([^,]*)$/, " and $1") + " mA cm⁻² at 50, 100, 500 and 1000 mL, so a litre-scale beaker tolerates " + xmul(THERM.volume_sweep.i_boil_mAcm2.DMF["1000"] / THERM.volume_sweep.i_boil_mAcm2.DMF["100"], 2) + " the current density of the 100 mL vessel specified in §S6; the 100 mL entry is the DMF beaker ceiling of §S6.1. Statements that the ceiling is independent of inventory hold only if UA is pinned while inventory changes, which is not physically realisable; the beaker rows of §S6 are therefore specified as a 100 mL vessel (σ = " + SIG_B.toFixed(2) + ", from the wetted vessel area). Heat capacity does govern the transient, τ = m·c_p/UA, and this separates the architectures sharply: a 100 mL beaker of DMF has τ ≈ " + TAU_MIN(100).toFixed(0) + " min, whereas the 0.025 mL held in the 25 μm gap of the microfluidic archetype reaches its steady state in well under a second, passively or with active plates. Thin-gap cells therefore arrive some three orders of magnitude faster, so the thermal inertia that makes a beaker forgiving of a current excursion or a cooling interruption is absent by construction; the margins of panel (b) are reached essentially immediately. Batch scale cuts the other way for beakers: τ grows only as V^(1/3) (≈" + TAU_MIN(100).toFixed(0) + " min at 100 mL, ≈" + TAU_MIN(1000).toFixed(0) + " min at 1 L) while the charge-limited run time grows as V, so larger batches are the more likely, not the less likely, to sit at their steady-state temperature for most of the electrolysis. (iii) Recirculating architectures: in operation the flowing electrolyte relocates heat advectively — the single-pass rise q·A_e/(ṁ·c_p) is <1 K at 100 mA cm⁻² for DMF at 10 cm s⁻¹ — so the steady state is set by rejection at the reservoir or exchanger, and a recirculating loop restores the beaker-like time constant (τ ≈ 1 min for a 100 mL loop) without changing U′_req. (iv) Zero-gap idealisation: the stack entry treats the 100 μm separator as a gap filled with the bulk electrolyte, which is the like-for-like comparison across solvents but neglects membrane-specific conductivity and the tortuosity of porous electrodes; it should be read as the geometric limit of gap reduction rather than as a validated non-aqueous stack design."),

  h2("S6.3 Temperature dependence of conductivity"),
  p("The analysis above uses the 25 °C conductivities in Table S4, although the cells whose behaviour they predict are, by construction, approaching their boiling points — 66 °C for THF, 82 °C for MeCN, 100 °C for the aqueous reference, 153 °C for DMF. Conductivity rises with temperature, so holding κ at 25 °C overstates the ohmic heat generated at every operating point and therefore understates every boil-off ceiling. No temperature dependence of κ (or of μ) enters the thermal model, the cell-voltage stack or the transport correlations anywhere in the code. The resulting bounds are therefore one-sided: the ceilings of §S6.1 are conservative lower bounds and the cooling duties of §S6.2 are conservative upper bounds."),
  p("We bound the effect rather than correct it, because a correction would require κ(T) data we do not have for these compositions. Two effects compete as temperature rises: falling viscosity lets ions move faster, which raises κ (Walden, κ ∝ 1/μ), while the falling dielectric constant increases ion pairing, which holds κ back. A single Arrhenius or Walden law captures the first mechanism only, so it is an upper bound on the ceiling — this is also why the literature on organic liquid electrolytes reports that single-Arrhenius fits describe them poorly and that VFT-type forms are needed. The defensible statement is therefore a bracket: the lower end is κ fixed at 25 °C, the value used throughout §S6; the upper end is Arrhenius scaling of κ from 25 °C to the boiling point with an activation energy of 15 kJ mol⁻¹. That 15 kJ mol⁻¹ is a declared assumption, not a fitted or measured quantity, and its one piece of external support is an anchor on water, whose viscosity is well tabulated: μ = 0.890 cP at 25 °C and 0.282 cP at 100 °C, a ratio of 3.16, so Walden predicts κ × 3.16 at 100 °C, while Arrhenius at 15 kJ mol⁻¹ predicts × 3.37 — the two agree to 6.9%. Anything narrower than this bracket would require measured κ(T) for the specific electrolytes."),
  p("Applied at each solvent's boiling point the upper bound multiplies κ by 2.08 (THF), 2.63 (MeCN), 3.37 (aqueous NaOH) and 6.14 (DMF). The unstirred-beaker ceilings of §S6.1 then move from " + _sorder.map(x => ktCeil(KT_BEAKER, x).i_boil_25C.toFixed(0) + " to " + ktCeil(KT_BEAKER, x).i_boil_kappaT.toFixed(0)).join(", ").replace(/, ([^,]*)$/, " and $1") + " mA cm⁻² respectively, and across all " + KT.factor_range.n_pairs + " (architecture, solvent) pairs of §S6.1 the bracket spans a factor of " + f2(KT.factor_range.min) + " to " + f2(KT.factor_range.max) + ". " + (KT.factor_range.n_pairs - KT_FLIPS.length) + " of those pass/fail verdicts are identical at both ends of the bracket. The " + KT_FLIPS.length + " bound-dependent verdicts are " + KT_FLIPS.map(f => ktPair(f.reactor, f.solvent)).map((d, j) => T_PRETTY[KT_FLIPS[j].solvent] + " in the " + KT_FLIPS[j].reactor.replace("$\\mu$m", "μm") + " (" + d.i_boil_25C.toFixed(0) + " → " + d.i_boil_kappaT.toFixed(0) + " mA cm⁻² against " + d.i_design.toFixed(0) + ")").join("; ") + ". Each is flagged as bound-dependent wherever it appears, and none is reported as a finding. Those cells are very nearly the same ones the gap sweep of Table S7i finds conditional, which gives the combined implication of this analysis: the marginal architecture–solvent pairs are marginal on every axis at once, and no cell that clears comfortably at 25 °C is put at risk by the bracket. The qualitative conclusions — that transport binds before heat in the batch and thick-gap cells, that the two rotating archetypes cannot sustain their own transport ceilings in any organic solvent under passive cooling, that only thinning the gap raises the thermal ceiling, and that the zero-gap stack collapses on its own enclosed geometry — are robust to the omitted temperature dependence. The absolute ceilings are not, and should be read as lower bounds."),
  p("The DMF factor carries the weakest support of the four and should be treated separately. Its × 6.14 is an extrapolation of the Arrhenius coefficient across 128 K, from 25 °C to 152.8 °C, whereas the water anchor that licenses that coefficient was established across 75 K; it is also the factor that produces the largest single change in the table (" + ktCeil(KT_BEAKER, "DMF").i_boil_25C.toFixed(0) + " → " + ktCeil(KT_BEAKER, "DMF").i_boil_kappaT.toFixed(0) + " mA cm⁻² in the beaker, " + ktCeil(KT_MICRO, "DMF").i_boil_25C.toFixed(0) + " → " + ktCeil(KT_MICRO, "DMF").i_boil_kappaT.toFixed(0) + " mA cm⁻² in the microfluidic). Ion pairing in an amide solvent at 153 °C is precisely the regime in which the neglected dielectric term is largest, so the true DMF ceiling almost certainly sits well below the upper bound. No conclusion in this work rests on the DMF upper bound; it is quoted only to establish the width of the bracket. Every upper-bound number in this section is reproducible from this document alone: it is the boil-off current of Eqs. S20–S21, evaluated with exactly the geometry, σ, h_int and h_ext of §S6.1 and the Table S4 conductivity multiplied by exp[(E_a/R)(1/298.15 − 1/T_b)] with E_a = 15 kJ mol⁻¹. The full bracket for all " + KT.factor_range.n_pairs + " (architecture, solvent) pairs is computed at build time."),

  h2("S6.4 Inter-electrode gap and heat-rejection area"),
  p("Two terms in the heat balance carry no source for most of these cells: the inter-electrode gap and \u03c3. Neither is given an invented band. Each is swept and reported as a breaking point, the multiple of the declared value at which a verdict would reverse. \u03c3 is the tighter of the two, and " + TGEO.conditional_on_sigma.length + " verdicts turn over within a factor of 2.5 of it, all of them at an architecture that intensifies transport without changing the cell body. Those " + TGEO.conditional_on_sigma.length + " are reported as conditional wherever they appear."),
  p("One of the four has external corroboration, and it runs in the safe direction. The parallel H-cell of Table S5 is assembled from two polycarbonate compartments of 2 \u00d7 2 \u00d7 0.22 in with a 1 cm\u00b2 cathode, which gives 74.3 cm\u00b2 of outer surface over 1 cm\u00b2 of electrode, i.e. \u03c3 = 74.3 against the " + SIG_B.toFixed(2) + " this model carries.\u00ab" + "lobaccaro2016" + "\u00bb The value used here is conservative for that cell by a factor of " + (74.3 / SIG_B).toFixed(1) + ", and adopting the published one would only widen a margin that already clears, so it is not adopted: one exemplar body is not the archetype. The same is not available for the other three, whose exemplars state no external dimensions, so those rows keep the beaker value."),
  p("The gap admits a weaker but independent test. The same exemplar reports a measured cell resistance of 45\u201360 \u03a9 in 0.1 M KHCO\u2083, and at the 1 cm\u00b2 cathode of the cell it was built from, with the handbook's \u03ba = 8.9 mS cm\u207b\u00b9 at 20 \u00b0C (Table S7i) carried to 9.6\u20139.8 mS cm\u207b\u00b9 at 25 \u00b0C on the same 1.5\u20131.9%/K coefficient the aqueous rows of that table use, that corresponds to an ohmic path of 0.43\u20130.58 cm. That figure is a LOWER bound on the quantity the heat balance needs and not an estimate of it: the resistance is the uncompensated value between working and reference electrodes, whereas the Joule heat is dissipated across the full working-to-counter path, which is longer. The declared 2 cm sits above the bound, so the measurement is consistent with it without pinning it. Two conditions are stated rather than buried: the exposed area is taken from the cell this one modifies, not from the modifying paper, and the bound assumes the reference sits within the cathode compartment as described."),
  p("Finally, a simplification that is invisible here and would not be everywhere. The balance places the internal and external films in series and carries no conduction resistance through the vessel wall between them. For a 1.5 mm borosilicate beaker that term is 2 % of the series resistance, below the reporting precision of every ceiling in this section. For the 5.6 mm polycarbonate body just described it is 28 %, and including it would lower that cell's ceilings by about 15 %. No architecture in §S6 is computed on a plastic body, so no published number moves, but the term would have to be restored for any architecture with a thick low-conductivity wall."),
  h1("S7. Summary of limiting currents"),
  p("The full matrix applies the same physical model across all fifty rows: a one-dimensional steady Nernst–Planck balance with migration and local electroneutrality across the diffusion film, on dilute-solution theory (Newman, Ch. 11), galvanostatic; the eight mediated entries additionally carry the homogeneous EC′ source of §S5.5. All " + N_CELLS + " cells are converged solutions; none is reported at a numerical floor. The scope of the result follows from these assumptions: the model computes a transport ceiling, so it carries no electrode kinetics, and its film thickness is a lumped parameter from a mass-transfer correlation rather than a solved momentum boundary layer. What the migration term buys, measured against the same fifty rows solved without it, is a rise in the ≥25 mA cm⁻² count from " + ARCH.map(([, k]) => [k, ARCHLBL[k]]).map(([k,lab]) => fickCount(k,25) + " to " + MS.get(k).ge25 + " (" + lab + ")").join(", ") + ", and in the ≥50 mA cm⁻² count from " + ARCH.map(([, k]) => [k, ARCHLBL[k]]).map(([k,lab]) => fickCount(k,50) + " to " + MS.get(k).ge50 + " (" + lab + ")").join(", ") + ". The term is not uniformly important: 39 of the 50 carriers are neutral, and migration changes the ceiling by less than 5% on 40 of the 50 rows, by more than twofold on five." + " Every mediated EC′ value in Table S6 reaches the collapse criterion under concentration control, and §S5.6 measures the answer to move by at most 0.01% under a 7.5× finer continuation and a doubled mesh, so solver refinement cannot move these counts in either direction. A second and larger source of imprecision in these integers is not the solver but the property inputs: " + numw(SP.n_flagged) + " of the fifty rows run in a solvent whose viscosity and density are not page-anchored — the two HFIP rows, whose registry row carries no source at all, and " + numw(SP.n_flagged - 2) + " mixed-solvent rows whose properties are mixing-rule estimates. Because i_lim ∝ μ^p with p between −1 and −2⁄3 — exactly −1 for the two archetypes whose δ is declared, and −2⁄3, −5⁄6 and −0.988 for the Lévêque, Levich and Eisenberg correlations, where scaling μ moves ν and therefore δ as well and the two partly cancel — a ±25–50% error confined to those rows shifts each architecture's ≥25 mA cm⁻² count by at most " + numw(SP.worst_count_movement) + " entries of fifty (" + SP.baseline_per_arch.join("–") + " spans " + spSpan() + ") and the substrate-carried clearing count from " + SP.substrate_span[0] + "/" + SP.n_substrate + " to " + SP.substrate_span[1] + "/" + SP.n_substrate + ". **The counts should therefore be read as ±" + SP.worst_count_movement + " of 50, not as exact integers.** What does not move is the ordering: unstirred < stirred < flow < thin-gap holds at every point of that sweep, and every conclusion drawn here rests on the ordering and on the order-of-magnitude span, not on the individual counts "),
  mkTable(["Reactor archetype","median i_lim (mA/cm²)","≥ 25 mA/cm²","≥ 50 mA/cm²"],
    ARCH.map(([label, k]) => [label, med(k), ge25(k), ge50(k)]),
    [2500,2100,1300,1300]),
  cap("Table S5. Results across the 50-reaction set at the reported conditions of Table S2 (Stage-0 for direct entries and for the four catalyst-carried entries with no measured rate constant; EC′ solver for the mediated entries and for the seven catalyst-carried entries carried at a sourced rate constant, §S5.7). The 14 reactions below the 25 mA cm⁻² threshold in every architecture are the concentration-capped core: " + (SR ? ["zero","one","two","three","four","five","six","seven","eight","nine","ten","eleven"][11 - SR.rows_clearing25_anywhere] : "ten") + " of the eleven catalyst-carried entries (2.6–15 mM at the reported loadings; seven at their sourced rate constant and four at k = 0, §S5.7), the 25 mM ACT mediator (plateau at 22 mA cm⁻²), and three dilute-substrate academic protocols (a 0.02 M flow-kinetics study; the RAE-activated decarboxylative coupling, whose electrolysis concentration is 0.029 M once the SI's activation-step 0.2 M is unpacked; and the catalytic-in-electrons Diels–Alder). The single catalyst-carried entry that clears threshold is the 30 mM Ni aryl–aryl homocoupling (ref. ⟦courtois1997⟧); the kilogram-scale flow XEC system (ref. ⟦kelly2026⟧), verified at 15 mM Ni, is carried at the sourced k = 10² M⁻¹ s⁻¹ at the DMA viscosity CRC prints (1.927 mPa s, p. 6-244; a printed value that disagrees with its own homolog by a factor of two, Table S7b). " + ckXec() + " At k = 0 the same row's ceiling was ≈8 mA cm⁻² in the rotating-cylinder cell and below 1 in the recirculating-flow cell, i.e. below the current the campaign ran at; that gap was the k = 0 treatment, not the viscosity."),
  p("These thresholds are anchored in the pharmaceutical-industry survey of Ferretti et al.«ferretti2025» (17 companies surveyed): of the 14 that reported scale-up current densities (Fig. 11 therein), 10 operate below 25 mA cm⁻², three between 25 and 50, and one above 50 mA cm⁻². The model reproduces this operating reality and locates its cause: at the reported exemplar concentrations (modern academic scope rows cluster at 0.02–0.5 M; preparative-scale and industrial entries run 0.8–6.9 M), batch and standard flow reactors place the transport ceiling on the order of tens of mA cm⁻², the same order as the reported industrial operating window. This comparison is intentionally order-of-magnitude. The measured stirred-cell film of 200 \u00b1 7 \u03bcm gives a median of 9.1 mA cm\u207b\u00b2, but the overlapping unstirred-film range does not support a sharper distinction between the two batch archetypes. A direct measurement provides the more relevant bound. Williams and co-workers determine the mass-transport boundary layer of a gas-bubbled electrochemical cell directly \u2014 diffusion-limited ferricyanide current, back-calculated through i_lim = nFDc/\u03b4 \u2014 and obtain 200 \u00b1 7 \u03bcm for dissolved O\u2082 (Sustain. Energy Fuels 2019, 3, 1225, p. 1227). That is a planar electrode in a convecting cell, the same situation as this archetype, and O\u2082 diffuses about twice as fast as the bulky organics modelled here, so it should if anything give a thinner layer than they would. This measurement is the value the archetype uses, so the stirred ceilings rest on a measured film rather than an estimated one, and the direction of its residual error is known: a thicker true layer would lower them further. What it does not resolve is which batch archetype a claim would belong to, since the free-convection band for the unstirred cell overlaps it. Evaluating Levich \u03b4 = 1.61 D^1/3 \u03bd^1/6 \u03c9^\u22121/2 on each reaction\u2019s own D and \u03bd gives 15\u201336 \u03bcm across 200\u20131200 rpm, an order of magnitude below the measurement; that is the correct behaviour of a rotating disc, which is a uniformly accessible electrode in the most efficient laminar convection available, and it is not what a stationary plate in a stirred beaker sees. The idealised bound therefore sits an order of magnitude below the value in use, as it must, and the measurement is what the archetype rests on. A film thin enough to put the stirred median above 25 mA cm\u207b\u00b2 would have to be 2.9 times thinner than the measured cell, which nothing here brings within reach. A value of \u03b4_stirred below about 86 μm would make a stirred beaker outperform a parallel-plate flow cell and invert the architecture ranking this section rests on. That is a self-consistency argument, not evidence, and it is labelled as such. Crossing the 50 mA cm⁻² barrier that only one surveyed company has broken requires nothing more than the thin-film reactor architectures of Table S5: " + ge50("natural") + " reactions clear it in an unstirred cell, " + ge50("rce") + " at a rotating-cylinder electrode, with the chemistry and concentrations unchanged (§S6). The per-reaction engineering gap and the two-lever decomposition (reactor levers for substrate-carried chemistry; carrier-concentration levers for catalyst- and mediator-carried chemistry) are shown in §S6."),
  p("The carrier decomposition is the central mechanistic result: convection engineering rescues substrate-carried chemistry essentially without exception, while dilute-carrier chemistry is concentration-capped in every reactor — by the carrier where the homogeneous step is slow and by the dilute substrate where it is fast, with the seven rows carried at a sourced rate constant sitting between the two in the kinetic regime, where thinning the film buys a few-fold rather than the 1/δ of a transport-limited row (§S5.7). Raising the ceiling for that class requires raising the carrier concentration itself — precisely the strategy of recent high-concentration electron-mediator work — or decoupling the electrode event from the catalytic cycle (paired/ex-cell schemes). Gas-fed substrates (CO₂ carboxylation, propylene epoxidation) sit at the solubility-limited extreme of the same analysis, and gas-diffusion electrodes are the corresponding architectural remedy, as CO₂ electrolysis practice demonstrates."),

  h1("S8. Limitations"),
  p("The parameter table quantifies the data problem the main text describes: of the 50 diffusivities, 45 are correlation estimates (34 Wilke–Chang, 11 Stokes–Einstein) and 5 rest on measured limiting conductivities (Nernst–Einstein); none of the non-aqueous organic values has a direct experimental measurement in its actual working electrolyte. Concentrations are representative of exemplar reports rather than optimized values; activity corrections, ion pairing in low-ε solvents, and concentration-dependent viscosity are all outside dilute-solution theory; and the fixed-δ archetypes (unstirred, stirred) are order-of-magnitude conventions. None of these caveats disturbs the architecture ranking or the carrier dichotomy, which rest on ratios spanning one to two orders of magnitude, but all of them limit reaction-by-reaction precision. Machine-learned property prediction (e.g., Chemprop-class models trained on the sparse measured D data) and standardized reporting of D, κ, and solubility alongside synthetic results would upgrade this screening model into a quantitative design tool; the continuum frameworks developed for CO₂ electrolysis«bui2022» then translate directly."),
  p("The provenance registry of Table S7 makes that data problem quantitative rather than rhetorical, and its result belongs in the same place. Of the " + CENSUS_ALL.n + " registered parameters, " + CENSUS_ALL.measured + " are measured with a specific source locator, " + CENSUS_ALL.derived + " are derived from measured or derived inputs by a named method, and " + CENSUS_ALL.assumption + " are declared assumptions with a stated sensitivity. (These four counts, and every other census figure in this document, are generated from the registry at build time to maintain consistency between the prose and tables.)" + " This appendix tabulates the parameters that can support a stated claim, figure or table entry, and not the ones that exist only because the model was assembled incrementally: " + N_OMITTED + " further rows are carried in the machine-readable registry and omitted here. They are omitted by a stated rule rather than by selection — a row is set aside when the solvent it describes is used by none of the fifty reactions, or when its own registry text declares it display-only — and the rule is applied mechanically, and it also asserts that nothing load-bearing can be caught by it: no solver species, no conductivity carrying a §S6 verdict, and no solvent any reaction uses. The distinction is worth making because the union of the two sets misrepresents the weakest category. Counting every row, the electrolyte conductivities read " + CENSUS_COND_ALL.measured + " measured, " + CENSUS_COND_ALL.derived + " derived and " + CENSUS_COND_ALL.assumption + " assumption, which invites the conclusion that the ohmic and thermal analysis rests on that many unsourced numbers. It rests on four, and those four are the ones tabulated in Table S4 with the margin by which each would have to be wrong to overturn the verdict it carries. A fifth survives the filter for a different reason: 0.1 M Bu₄NBF₄ in DMF is quoted in the main text rather than used by any entry of the fifty, and is registered here so that the worked example built on it can be checked. The remaining conductivities are attached to reactions but drive nothing that is reported here, because κ enters no transport quantity: Eq. S1 and the Nernst–Planck and EC′ solvers use D, C, δ and z only." + (LEDGER ? " That last figure is the one most open to misreading, so it is broken out rather than left as a total. Sorting the " + LEDGER.n_assumption_live + " state-C rows of this appendix by what actually backs each one: " + [(LEDGER.counts_live.T0 ? LEDGER.counts_live.T0 + " are consumed but a named gate establishes they cannot move a reported conclusion" : null), (LEDGER.counts_live.T1 ? LEDGER.counts_live.T1 + " are declared choices rather than measurements of anything \u2014 the reactor archetypes, the solver discretisation and the isothermal operating point \u2014 validated by convergence and sweep studies because no citation could support them" : null), (LEDGER.counts_live.T2 ? LEDGER.counts_live.T2 + " state a perturbation and its computed effect, and the conclusion survives the stated range" : null), (LEDGER.counts_live.T3 ? LEDGER.counts_live.T3 + " do the same but the row itself records that a conclusion is conditional on where the value sits in its band, and those are the rows to read first" : null), (LEDGER.counts_live.T4 ? LEDGER.counts_live.T4 + " give no magnitude but fix the sign, so that no magnitude of the term could reverse the inequality claimed" : null), (LEDGER.counts_live.T5 ? LEDGER.counts_live.T5 + " fail the standard\u2019s own test of carrying a perturbation and its effect" : null)].filter(Boolean).join("; ") + ". " + (LEDGER.counts_live.T5 ? "" : "No row of this appendix fails that test. ") + "The classification is derived from the registry text by a published rule rather than assigned row by row, and the rule is checked in both directions: a blanked sensitivity, a bare cross-reference and the unsupported word \u201cconservative\u201d all fall to the lowest class." : "") + " The assumptions are not evenly spread. Of the " + CENSUS_COND.n + " electrolyte conductivities this appendix publishes, " + CENSUS_COND.measured + " are measured, " + CENSUS_COND.derived + " derived and " + CENSUS_COND.assumption + " an assumption — a position reached only in the final provenance pass, and one that still leaves the conductivity of a preparative organic electrolyte the hardest number in this work to source. So are "  + CENSUS_DIFF.assumption + " of the " + CENSUS_DIFF.n + " solver-species diffusivities in non-aqueous media and every mixture viscosity and density. Three quantities carry no citation, and are declared assumptions for that reason: the natural-convection film thickness, the stirred-cell film thickness and the cooling duty of a PEM-class stack. No source consulted tabulates either film thickness, and the cooling duties in circulation for such a stack span an order of magnitude, so each of the three is given in Table S7 with a sensitivity in place of a reference. The concentrated aqueous conductivities are cited to \"Electrical Conductivity of Aqueous Solutions\", CRC Section 5, p. 5-71, which tabulates 0.5–50 mass %; the equivalent-conductivity table at p. 5-74 is at 25 °C and stops at 0.1 M, so it cannot reach these concentrations. On that basis four aqueous rows are derived rather than assumed (§S6.1, Table S4). Two conclusions flip inside the range of an input they rest on, and are stated conditionally in §S6.2 and §S7. What survives is what the analysis was for: an architecture ranking and a carrier dichotomy that rest on ratios of one to two orders of magnitude, and that are stable across every sensitivity band in Table S7."),
  h2("S8.1 Conversion per pass and pressure drop"),
  p("A limiting current density is a flux, and the quantities that decide whether a reactor is "
    + "useful are a productivity and the cost of achieving it. Those move differently from the "
    + "flux, and in one case they move in the opposite direction, so they are computed here for "
    + "a declared pair of generic laminar parallel-plate channels \u2014 1 mm / 5 cm / "
    + "5 cm s\u207b\u00b9 and 250 \u00b5m / 2.5 cm / 10 cm s\u207b\u00b9 (Table S7g) \u2014 chosen to span a "
    + "fourfold gap step; none of the archetypes of Table S1 is computed from them, and the "
    + "L\u00e9v\u00eaque correlation that describes them is the one the microfluidic archetype's "
    + "half-gap floor is checked against. Residence time is \u03c4 = L/u; conversion per pass for plug flow with a "
    + "wall sink and specific area a = 1/h is X = 1 \u2212 exp(\u2212k_m\u03c4/h); the laminar "
    + "pressure drop between parallel plates is \u0394P = 12\u03bcuL/h\u00b2. At the median carrier diffusivity of the 50-reaction set the two channels give \u03b4 = " + f2(reA.delta_um) + " and "
    + f2(reB.delta_um) + " \u00b5m, \u03c4 = " + f2(reA.tau_s) + " and " + f2(reB.tau_s) + " s, "
    + "conversion per pass " + f2(100*reA.conversion_per_pass) + "% and "
    + f2(100*reB.conversion_per_pass) + "%, and \u0394P = " + f2(reA.dP_Pa/1000) + " and "
    + f2(reB.dP_Pa/1000) + " kPa."),
  p("Comparing the 1 mm and 250 \u00b5m channels shows that thinning the gap changes these "
    + "quantities differently. The thinner gap lowers \u03b4 by " + f2(reR.delta)
    + "\u00d7 and raises flux by approximately the same factor. Although the residence time "
    + "decreases by " + f2(1/reR.tau) + "\u00d7, the specific area a = 1/h increases by the "
    + "same factor, so conversion per pass rises by " + f2(reR.X_pass) + "\u00d7. The tradeoff "
    + "is pumping: \u0394P scales as 1/h\u00b2 at fixed velocity and rises " + f2(reR.dP)
    + "\u00d7. Gap reduction therefore improves both flux and conversion per pass in this "
    + "comparison, while increasing pressure drop and fabrication demands."),
  p("Two cautions attach to these numbers. Plug flow with a wall sink overstates conversion "
    + "relative to a real velocity profile, which is the direction that does not flatter "
    + "intensification; and \u0394P is the fully developed laminar result, excluding entrance "
    + "effects and manifolding, so it is a lower bound on real pumping cost. Both single-pass "
    + "conversions are small in absolute terms \u2014 under 5% \u2014 which is why flow cells in this "
    + "field are run with recirculation rather than in a single pass, and why a per-pass number "
    + "should never be read as a batch yield."),

  ...s9,

  h1("S10. Bounds on reported quantities"),
  p("Each quantity reported in the main text is given below with a lower and an upper bound, obtained by recomputing it at the limits of the ranges assigned to its dominant input in Table S7. The model is re-evaluated at those limits rather than linearised about the central value."),
  p("Transport and thermal quantities are bounded differently because they scale differently. For the seven architecture medians and the \u226525 and \u226550 mA cm\u207B\u00B2 counts the dominant input is the diffusion-layer thickness, taken over \u03B4 = 124\u2013439 \u03BCm (unstirred, the envelope over the correlation's declared height and driving force), 193\u2013207 \u03BCm (stirred, the measurement\u2019s own uncertainty), \u00b112.1 % about the measured 106.9 and 36.2 \u03BCm (recirculating and ANEC flow cells, the replicate scatter the same study reports for its one replicated cell), the printed residence-time range 4\u201312 min (microfluidic cell, over which the half-gap film does not move), 400\u20133600 rpm (RDE) and 1000\u20135000 rpm (rotating cylinder). For the 42 reactions treated by the Nernst\u2013Planck film model i_lim \u221D 1/\u03B4 exactly, so those columns rescale with \u03B4. For the eight mediated entries it does not: the catalytic amplification i_ec/i_t0 depends on \u03B4/x_k and varies by up to three orders of magnitude across the \u03B4 range for the fastest systems, so each is re-solved at both limits."),
  p("For the Fig. 5 boil-off ceilings, zero-gap currents and cooling-duty ratios the dominant input is the electrolyte conductivity, taken over the band given for each electrolyte in Table S4. Two further model choices widen those bands: the internal film coefficient h_int, over 50 W m\u207B\u00B2 K\u207B\u00B9 to the well-stirred limit, moves every ceiling by \u22125/+6%; and evaluating the external film at the boiling point rather than at ambient raises ceilings by \u22120.1% (THF), +3.5% (MeCN), +15.7% (DMF) and +7.3% (aqueous NaOH)."),
  p("One bound is one-sided. The conductivity of 3.0 M LiBr in THF has a measured floor, \u03BA(0.3162 M) = 0.256 mS cm\u207B\u00B9, and \u03BA rises with concentration up to the conductivity maximum; no measurement bounds it from above at the working concentration. The lower bound on the THF ceilings is therefore a floor rather than a limit; the THF verdicts that fail reverse only above " + THF_BIND[1].kappa_reverse_mScm.toFixed(1) + " mS cm\u207B\u00B9 (the " + ARCH_SHORT(THF_BIND[0]) + ")."),
  mkTable(["Reported quantity", "Lower", "Reported", "Upper", "Input varied"],
    Object.keys(BOUNDS.transport).map(k => {
      const v = BOUNDS.transport[k];
      const m = k.match(/^(median|count >=\d+), (\w+)$/);
      const nm = m ? (m[1].startsWith("median") ? "median i_lim, " : "count clearing " +
                      m[1].replace("count >=", "") + " mA cm\u207B\u00B2, ") + ARCHLBL[m[2]] : k;
      return [nm, bnum(v.lower), bnum(v.value), bnum(v.upper), "diffusion-layer thickness \u03B4"];
    }), [4200, 1300, 1300, 1300, 3600]),
  cap("Table S8. Bounds on the transport quantities of the main text, evaluated with every architecture at the current-minimising and current-maximising limit of its \u03B4 range. Medians in mA cm\u207B\u00B2; counts out of 50."),
  mkTable(["Reported quantity", "Lower", "Reported", "Upper", "Input varied"],
    Object.keys(BOUNDS.thermal).map(k => {
      const v = BOUNDS.thermal[k];
      return [k + (v.one_sided ? " (one-sided)" : ""), bnum(v.lower), bnum(v.value), bnum(v.upper),
              "\u03BA of " + v.registry_row.replace(/ \(.*/, "")];
    }), [4200, 1300, 1300, 1300, 3600]),
  cap("Table S9. Bounds on the thermal quantities of Fig. 7. Ceilings and zero-gap currents in mA cm\u207B\u00B2; cooling shortfalls are the ratio U\u2032_required(i_design)/U\u2032_passively available. Rows marked one-sided have no upper bound on the conductivity, so the lower bound on the ceiling is a floor."),
  p("Three features of these bounds bear on how the results should be read. The architecture ranking is stable throughout: the medians remain ordered " + ORDERING_TEXT + " at both limits, and it is that ordering, not the individual values, that the analysis rests on. The three thin-film medians lie within " + Math.round(100 * (Math.max(...ORDER_THIN.map(k => MS.get(k).median)) / Math.min(...ORDER_THIN.map(k => MS.get(k).median)) - 1)) + "% of one another and are not claimed to be ordered among themselves; the rotating-disc/rotating-cylinder pair is the one the second correlation of §S3.3 inverts, and that is disclosed there. The counts are less stable \u2014 the \u226525 mA cm\u207B\u00B2 count in an unstirred cell spans " + bnum(BOUNDS.transport["count >=25, natural"].lower) + "\u2013" + bnum(BOUNDS.transport["count >=25, natural"].upper) + " of 50 about a central " + bnum(BOUNDS.transport["count >=25, natural"].value) + ", and the stirred count " + bnum(BOUNDS.transport["count >=25, stirred"].lower) + "\u2013" + bnum(BOUNDS.transport["count >=25, stirred"].upper) + " about " + bnum(BOUNDS.transport["count >=25, stirred"].value) + " \u2014 so a count indicates the order of how many reactions are transport-limited rather than a precise tally. And the microfluidic cell now clears by a wide margin on this axis too: the cooling duty DMF needs there spans " + bnum(BOUNDS.thermal["DMF 25 um cooling shortfall"].lower) + "\u2013" + bnum(BOUNDS.thermal["DMF 25 um cooling shortfall"].upper) + " times what that cell rejects unaided, so passive cooling suffices across the whole conductivity band."),
  p((() => {
    // Computed from results/substrate_D_sensitivity.json (2026-09-14). This paragraph typed the
    // bromination cell at 25.3 mA cm-2 and a 12 -> 11 count move from the 300 um unstirred film;
    // on the 228 um film that cell reads 33.3 and the sweep moves different counts.
    const SD = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "substrate_D_sensitivity.json"), "utf8"));
    const moves = [];
    SD.scales.forEach(sc => Object.keys(SD.base_counts).forEach(a => [0, 1].forEach(t => {
      const b = SD.base_counts[a][t], v = SD.counts[String(sc)][a][t];
      if (v !== b) moves.push(a.replace(/ \(25 um gap\)/, "").replace(/^(Recirculating|Unstirred|Stirred|Microfluidic|Rotating)/, w => w.toLowerCase()) + " \u2265" + (t ? 50 : 25) + " mA cm\u207B\u00B2 count " + b + " \u2192 " + v + " of the eight at \u00D7" + sc);
    })));
    const cc = SD.closest_cell_to_25;
    return "A further sensitivity acts through a different input: the substrate diffusivities of the eight mediated entries, which are Wilke\u2013Chang estimates. Scaling all eight together by \u00D7" + SD.scales[0] + " and \u00D7" + SD.scales[1] + " and re-solving the mediated matrix "
      + (moves.length ? "moves " + moves.join("; ") + ", and no count by more than one entry" : "moves no count")
      + ". The mediated cell closest to 25 mA cm\u207B\u00B2 is " + cc.reaction.replace(" -> ", " \u2192 ") + " in the " + cc.reactor.replace(/ \(25 um gap\)/, "").toLowerCase().replace("microfluidic cell", "microfluidic cell") + " at " + cc.i_mAcm2.toFixed(1) + " mA cm\u207B\u00B2, " + cc.margin_pct_to_25.toFixed(1) + "% above the threshold.";
  })()),

  h1("S11. Construction of the main-text figures"),
  p("Each main-text figure is computed from the inputs and results tabulated in this SI, re-plotted from a published data table, or drawn as a schematic. This section gives the source of every panel."),
  p("**Figure 1.** Panels (a)–(c) are computed from the dataset of §S4.1. Panel (a) counts distinct transformations by the earliest reported year retained on deduplication, per year and cumulatively. Panel (b) sorts the atom-mapped records into the transformation classes of §S4.1 and divides each class by the net redox change of its substrate ledger. Panel (c) gives, among the records that report each field, the share run in an undivided cell, under constant-current control, and by direct rather than mediated electron transfer; mediation is identified from each record's reagent and catalyst entries, so the mediated share is a lower bound. Panel (d) is a four-step funnel on logarithmic widths: the dataset total, the reactions demonstrated at 20 g or more reported by Lehnherr and Chen«lehnherr2024», the kilogram-scale pharmaceutical programmes reported by Kelly et al.«kelly2026», and the absence of a commercialized process among the companies surveyed by Ferretti et al.«ferretti2025»"),
  p("**Figures 2, 3 and 8** are schematics drawn for this work. Figure 2 summarises the interfacial mechanisms of main-text Section 2.1 and Figure 8 the component-level failure modes of Section 6; neither asserts a magnitude. Figure 3 summarises the case studies of Section 2.2, whose sources are cited there."),
  p("**Figure 4.** Panel (a) is a schematic of the reactor archetypes. Panel (b) places each of the seven modelled architectures at the median, over the fifty reactions, of its diffusion-layer thickness from the correlations and measured films of Table S1, against its median limiting current from Table S5. Panel (c) is a Nernst–Planck solve (§S5.1) of a representative reaction on the stirred-batch film, drawn at a sequence of applied currents approaching its limiting current."),
  p("**Figure 5.** Panel (a) solves the Nernst–Planck problem of §S5.1 for a representative reaction on the median film of each architecture, at 50 mA cm⁻² where a steady state exists and at the architecture's own limiting current where it does not; dashed curves mark the latter. Panel (b) plots the limiting current of every reaction in every architecture from the matrix of Table S5, coloured by carrier class; the mediated and catalyst-carried entries are the EC′ solves of §S5.5 and §S5.7."),
  p("**Figure 6.** Panels (a)–(c) are schematics. Panels (d)–(f) are EC′ solves (§S5.4) of three mediated entries of Table S6 at their cited rate constants on the ANEC film of Table S1, drawn at the limiting current; the regime named on each panel is read from the solve, and the grey curve is the local homogeneous reaction rate. Panel (g) repeats those three solves across the archetype films, and panel (h) does the same for three catalyst-carried entries at the rate constants of §S5.7."),
  p("**Figure 7.** All four panels are computed from the lumped energy balance of §S6.1, using the thermal parameters of Table S7i and the conductivities of Table S4. No single reaction is modeled: heat is generated only by the ohmic and electrode-overpotential terms of Eq. S20, with the illustrative electrode kinetics of Eq. S18, in each of the four electrolytes of Table S4, and each architecture is run at its median limiting current from Table S5. Panel (a) is the boil-off current density of each electrolyte in the unstirred beaker. Panel (b) divides each architecture's boil-off ceiling by its median limiting current from Table S5. Panel (c) evaluates the boil-off ceiling across interelectrode gaps at one declared heat-rejection geometry. Panel (d) is the heat-rejection coefficient required to hold each architecture at its limiting current without boiling (§S6.2), marked against what that cell rejects passively."),
  p("**Figure 9.** Panels (c) and (d) re-plot the per-device yields that Górski et al.«gorski2025» tabulate in their supporting information; the mean, standard deviation and per-device current are recomputed from that table and reproduce the summary that work prints, with the current taken at unit Faradaic efficiency and two electrons per bromination as it states. Panel (a) is a schematic of the device and panel (b) the assay reaction under that work's conditions."),
  p("**Figure 10.** Panel (a) redistributes the counts of Figure 1(d) across the readiness ladder of main-text Section 9, with the industrial processes named in the main text on the top rungs. Panel (b) is the architecture summary of Table S5: the median limiting current and the number of reactions above 25 mA cm⁻²."),

  h2("Code and data availability"),
  p("All calculations in Sections S1\u2013S10, including the transport, EC\u2032, and thermal models and every figure in Section 4, use only the inputs tabulated in this SI, require no restricted data, and use no third-party numerical library. Main-text Figure 1 is subject to a separate data-access limitation. It was generated from reaction-level records derived from CAS content accessed through SciFinder under a limited data use agreement, which permits publication of aggregate statistics and the rendered figure but not the underlying per-record data. Independent verification is therefore possible for the aggregate outputs, including the dataset size (25,941 distinct transformations), the class counts and polarity shares in Fig. 1b, the condition fractions in Fig. 1c, and the funnel counts in Fig. 1d. The deterministic pipeline reproduces these outputs in a pinned environment (Python 3.13, RDKit 2026.3.5, pandas 3.0.5, NumPy 2.5.1, PyArrow 25.0.0); the RDKit version is specified because 20 of 21,459 polarity labels change on an earlier release. Table S2, Table S7, and all parameter counts reported in the text are generated from the same two CSV files to maintain consistency between the prose and the tabulated data."),
  h1("References"),
  ...REFS.map((r, i) => new Paragraph({
    children: [new TextRun({ text: (i + 1) + "  ", size: 18, font: "Calibri" }),
               ...r.s.map(sg => new TextRun({ text: sg.t, size: 18, font: "Calibri", italics: !!sg.i, bold: !!sg.b }))],
    spacing: { after: 40 }, indent: { left: 420, hanging: 420 } })),
];

if (SI_MODE !== "condensed") auditRefOrder();


// ---- sentence splitter shared by the condensed build and its inventory (2026-09-14) ----------
// Splits prose at sentence ends without breaking on abbreviations, initials or decimals, so the
// condensed SI can keep whole sentences of the detailed one verbatim.
const ABBR = ["e.g", "i.e", "et al", "Fig", "Figs", "Eq", "Eqs", "ref", "Ref", "refs", "vs", "ca", "cf", "p", "pp", "No", "vol", "Vol", "ed", "Ch", "Sect", "cyl", "prio", "approx", "Chem", "Soc", "Am", "J", "Int", "Ed", "Res", "Dev", "Eng", "Sci", "Lett", "Commun", "Acta", "Phys", "Trans", "Data", "Org", "Process", "Electrochem", "Rev", "Nat", "Energy", "Environ", "Mater", "Ind", "Bull", "Ser", "Univ", "Proc", "Acc", "Soln", "Solution", "Faraday", "Z", "Angew", "Adv", "Front", "Curr", "Opin", "Catal", "Green", "Sustain", "Biomol", "Annu", "Heat", "Mass", "Transfer", "Fuels", "Sources", "Power", "Kagaku", "Kogaku", "Appl", "Mol", "Chim", "Ref", "Stand"];
function splitSentences(text) {
  const out = []; let start = 0;
  const re = /([.!?])(["”’»⟧)]*)\s+(?=[A-Z(«"“0-9†‡§*Λλκδσμ])/g; let m;
  while ((m = re.exec(text)) !== null) {
    const end = m.index + 1 + m[2].length;
    const before = text.slice(start, m.index);
    const lastTok = (before.match(/([A-Za-z]+)$/) || [])[1] || "";
    if (m[1] === "." && (ABBR.includes(lastTok) || /(^|[\s(])[A-Z]$/.test(before) || /\d$/.test(before) && /^\d/.test(text.slice(re.lastIndex)))) continue;
    out.push(text.slice(start, end)); start = re.lastIndex;
  }
  if (start < text.length) out.push(text.slice(start));
  return out;
}
if (process.env.SI_SENTENCES) {
  const inv = [];
  [["front", front], ["tableS2", tableS2], ["back", back]].forEach(([part, arr]) => arr.forEach((el, i) => {
    if (el.__kind === "p" || el.__kind === "cap") inv.push({ part, i, kind: el.__kind, s: splitSentences(el.__t) });
    else inv.push({ part, i, kind: el.__kind || "raw", t: (el.__t || "").slice(0, 120), cells: el.__cells });
  }));
  fs.writeFileSync(process.env.SI_SENTENCES, JSON.stringify(inv, null, 1));
}

if (process.env.SI_INVENTORY) {
  const inv = [];
  [["front", front], ["tableS2", tableS2], ["back", back]].forEach(([part, arr]) => arr.forEach((el, i) =>
    inv.push({ part, i, kind: el.__kind || "raw", lvl: el.__lvl || 0,
               len: (el.__t || "").length + (el.__cells || "").length, t: el.__t || "" })));
  fs.writeFileSync(process.env.SI_INVENTORY, JSON.stringify(inv, null, 1));
}

// ================================================================================================
// CONDENSED SI (SI_MODE=condensed), 2026-09-14.
// Author: "a condensed SI for pre-review that just has the essentials. The modeling details, all of
// the parameters and their provenance, and how all the figures were made in the MS" / "every
// equation, every parameter and its provenance should be in the SI for sure" / "it just needs to be
// so much shorter" / provenance as "Source, Page Number, Table".
// Built from the detailed SI's own elements: every equation and the section numbering are reused,
// prose is whole sentences selected from the detailed paragraphs (plus a few short linking sentences
// and captions written here), Table S7 carries every published parameter with a short locator from
// results/si_short_locators.json, and the reference list is renumbered by first appearance in the
// condensed document. data/check_si_condensed.py (G-SICOND) checks the result against the detailed SI.
// ================================================================================================
let DOC_FRONT = front, DOC_TABLES2 = tableS2, DOC_BACK = back;
if (SI_MODE === "condensed") {
  const SL = JSON.parse(fs.readFileSync(path.join(__dirname, "results", "si_short_locators.json"), "utf8"));
  const ALL = [...front, ...tableS2, ...back];
  const one = (hits, label) => { if (hits.length !== 1) throw new Error("condensed plan: " + label + " matched " + hits.length + " elements"); return hits[0]; };
  const P = (pre) => one(ALL.filter(e => e.__kind === "p" && e.__t.startsWith(pre)), "paragraph «" + pre + "»");
  const C = (pre) => one(ALL.filter(e => e.__kind === "cap" && e.__t.startsWith(pre)), "caption «" + pre + "»");
  const EQ = (tag) => one(ALL.filter(e => e.__kind === "eq" && e.__t === "(" + tag + ")"), "equation " + tag);
  const H = (pre) => one(ALL.filter(e => e.__kind === "h" && e.__t.startsWith(pre)), "heading «" + pre + "»");
  const T = (pre, nth = 0) => { const hits = ALL.filter(e => e.__kind === "table" && e.__t.startsWith(pre)); if (!hits[nth]) throw new Error("condensed plan: table «" + pre + "» #" + nth); return hits[nth]; };
  const CELLS = (tb) => tb.__cells.split("\n").map(r => r.split(" | "));
  const pick = (text, pres, label) => pres.map(pre => one(splitSentences(text).filter(x => x.startsWith(pre)), label + " sentence «" + pre + "»")).join(" ");
  const KEEP = (pre, pres) => p(pick(P(pre).__t, pres, "«" + pre + "»"));
  const KEEPCAP = (pre, pres) => cap(pick(C(pre).__t, pres, "«" + pre + "»"));
  const refsIn = (s) => { const ks = []; (s.match(/«([^»]+)»|⟦([^⟧]+)⟧/g) || []).forEach(m => m.slice(1, -1).split(",").forEach(k => { k = k.trim(); if (!ks.includes(k)) ks.push(k); })); return ks; };
  const regLoc = (name) => { if (!(name in SL.registry)) throw new Error("condensed Table S7/S4: no short locator for '" + name + "'"); return SL.registry[name]; };

  // ---- front matter: title page, S1-S4 ----
  const titleEnd = front.indexOf(H("S1. "));
  const qStart = front.indexOf(P("**Stage 1, topic query.**")) + 1, qEnd = front.indexOf(P("The exclusions remove adjacent"));
  const s1Table = CELLS(T("Archetype"));
  const S1_SOURCE = [
    "derived (Wilke, Eisenberg & Tobias 1953, Eq. XVII)",
    "measured on a proxy system (Williams et al. 2019, p. 1227)",
    "measured (⟦watkins2023⟧, SI Table S1)",
    "measured (⟦watkins2023⟧, SI Table S1)",
    "derived (⟦mo2020⟧, SI p. 13)",
    "measured (⟦bard⟧, p. 30)",
    "measured (⟦eisenberg⟧, p. 313)"];
  if (s1Table.length !== S1_SOURCE.length) throw new Error("condensed Table S1: row count changed");
  const s4Table = CELLS(T("Electrolyte | κ"));
  const s2Rows = CELLS(tableS2[0]);
  if (s2Rows.length !== SL.table_s2.length) throw new Error("condensed Table S2: " + s2Rows.length + " rows against " + SL.table_s2.length + " locators");
  DOC_FRONT = [
    ...front.slice(0, titleEnd),
    H("S1. "),
    KEEP("We quantify the transport-limited", ["We quantify the transport-limited", "Stage 0 evaluates", "Stage 1 resolves", "A companion module", "All calculations are implemented"]),
    p("Stage 2 adds the homogeneous chemical step for the mediated and catalyst-carried entries (§S5.4 and §S5.7)."),
    H("S1.1 "),
    KEEP("Four modelling choices define", ["Four modelling choices define"]),
    KEEP("(i) The transport problem", ["(i) The transport problem", "This treatment is necessary"]),
    KEEP("(ii) The viscosity is the", ["(ii) The viscosity is the", "μ in Table S3 is the"]),
    KEEP("(iii) The model computes", ["(iii) The model computes", "There is no electrode kinetics", "Electrode kinetics are omitted"]),
    KEEP("(iv) The diffusion layer", ["(iv) The diffusion layer", "δ is a measured film"]),
    KEEP("The numerical implementation is verified", ["The numerical implementation is verified"]),
    H("S2. "),
    P("The limiting current density for a species that must reach"), EQ("S1"),
    KEEP("where D_c and C_c are", ["where D_c and C_c are", "We classify every reaction by its carrier"]),
    KEEP("δ is obtained per reactor archetype", ["δ is obtained per reactor archetype", "Where a correlation applies"]),
    mkTable(["Archetype", "Model", "Geometry / operating point", "Correlation", "Source"],
      s1Table.map((r, i) => [r[0], r[1], r[2], r[3], S1_SOURCE[i]]), [1400, 1350, 1900, 1900, 2170]),
    cap("Table S1. Reactor archetypes and the source of δ for each. δ is evaluated per species from its D and the solvent ν. Values and locators: Table S7g."),
    H("S3. "), H("S3.1 "),
    P("Direct measurements of diffusion coefficients"), EQ("S2"),
    KEEP("with solvent molar mass M_B", ["with solvent molar mass M_B"]),
    P("Three carrier types receive dedicated treatment."),
    KEEP("Supporting-electrolyte ions in solvents", ["Supporting-electrolyte ions in solvents", "Because a supporting ion carries no flux"]),
    H("S3.2 "),
    T("Solvent | M"),
    cap("Table S3. Solvent properties used in Eq. S2 and in ν = μ/ρ for the reactor correlations. Only the product φM enters Eq. S2, so for the mixtures the tabulated M and φ are a split of the Perkins–Geankoplis product (ref. ⟦poling⟧, Eq. 11-9.8). Values, states and locators: Table S7b."),
    mkTable(["Electrolyte", "κ (mS/cm)", "State", "Source"],
      s4Table.map(r => [r[0], r[1], r[2], regLoc(r[0].replace(/ \/ /g, "/").replace(" (aq)", " aq"))]), [2200, 900, 1000, 5620]),
    cap("Table S4. Ionic conductivities (25 °C) used in the ohmic and thermal analysis of §S6. The derivation of the NaI/DMF value is given with Eq. S27; values, states and locators: Table S7f."),
    H("S3.3 "),
    KEEP("Table S1 gives each archetype its correlation", ["Eisenberg, Tobias and Wilke state their own calibration", "The fifty rows here run Sc", "The Reynolds number at this operating point"]),
    KEEP("We bound this extrapolation with a second", ["We bound this extrapolation with a second", "Jang and co-workers", "Eisenberg is retained as the primary"]),
    KEEP("The difference between the correlations", ["Per row the second correlation gives"]),
    H("S4. "), H("S4.1 "),
    KEEP("The dataset plotted in main-text Figure 1", ["The dataset plotted in main-text Figure 1"]),
    P("**Stage 1, topic query.**"), ...front.slice(qStart, qEnd),
    P("The exclusions remove adjacent"), P("**Stage 2, reaction filter.**"), P("**Deduplication.**"),
    P("**Atom mapping.**"), P("**Classification.**"), P("**Redox assignment.**"),
    P("**Scale and readiness.**"),
    H("S4.2 "),
    KEEP("The set is stratified by the reaction-class", ["The set is stratified by the reaction-class", "Two of the fifty rows fall outside", "Set share against dataset share", "On that basis the set is approximately"]),
    p("Every concentration, solvent and electrolyte in Table S2 is taken from the standard or scaled conditions of the named exemplar and converted to molarity from the stated amounts and volumes; the locator for each row is given in Table S2."),
    KEEP("The set is stratified by the reaction-class", ["Forty-eight of the fifty rows are verified this way"]),
    cap("Table S2 (following pages, landscape). The 50-reaction set: carrier assignment, carrier charge z at the electrode, carrier diffusivity and its estimation method (§S3.1), concentration, electrons per carrier turnover n_c, solvent, electrolyte and source. " + pick(C("Table S2 (following pages").__t, ["Four rows, marked *"], "Table S2 caption") + " The source column gives the exemplar reference and the page, table or figure of the conditions used."),
  ];
  DOC_TABLES2 = [
    mkTable(["#", "Class", "Reaction", "Carrier", "Carrier species", "z", "D (cm²/s)", "C (M)", "n_c", "Solvent", "Electrolyte", "D method", "Source"],
      s2Rows.map((r, i) => [...r.slice(0, 12), "[⟦" + ROWKEYS[i] + "⟧]" + (SL.table_s2[i] ? " " + SL.table_s2[i] : "")]),
      [400, 1000, 2600, 850, 1400, 350, 950, 650, 450, 950, 1600, 1450, 1390], 14040),
  ];

  // ---- back matter: S5-S11 ----
  const s6Rows = CELLS(T("Mediated system"));
  const catRowsC = CELLS(T("Catalyst-carried entry"));
  const catHdr = T("Catalyst-carried entry").__t.split(" | ");
  const s7Tabs = ALL.filter(e => e.__kind === "table" && e.__t.startsWith("Parameter | Value | Units | State"));
  const s7Caps = ALL.filter(e => e.__kind === "cap" && /^Table S7[a-k]\. /.test(e.__t));
  if (s7Tabs.length !== s7Caps.length) throw new Error("condensed Table S7: " + s7Tabs.length + " tables against " + s7Caps.length + " captions");
  const S7C = [];
  s7Tabs.forEach((tb, i) => {
    S7C.push(mkTable(["Parameter", "Value", "Units", "State", "Eq.", "Source"],
      CELLS(tb).map(r => [r[0], r[1], r[2], r[3], r[4], regLoc(r[0])]), [2300, 1000, 800, 900, 600, 4120]));
    S7C.push(cap(pick(s7Caps[i].__t, ["Table S7", s7Caps[i].__t.split(". ")[1].slice(0, 12)], "Table S7 caption")));
  });
  const sec11 = back.slice(back.indexOf(H("S11. ")), back.indexOf(H("References")));
  DOC_BACK = [
    H("S5. "), H("S5.1 "),
    P("Within the film 0 ≤ x ≤ δ we solve"), EQ("S3"), P("Conservation of mass for every species j"), EQ("S4"),
    P("where the single homogeneous step has"), EQ("S5"), P("with stoichiometric coefficients ν_ox"), EQ("S6"),
    P("Conservation of charge is not imposed separately"), EQ("S7"), P("so the current entering at the electrode"), EQ("S8"),
    KEEP("the first being the galvanostatic electrode condition", ["the first being the galvanostatic electrode condition"]),
    H("S5.2 "),
    P("The film is discretized in N finite volumes"), EQ("S9"), P("and the discrete statement of Eq. S4"), EQ("S10"),
    KEEP("with the electrode face flux replaced", ["with the electrode face flux replaced", "The unknowns are the logarithms", "The nonlinear system F(u) = 0"]),
    EQ("S11"), P("with a dense forward-difference Jacobian"),
    H("S5.3 "), P("Two analytic limits constrain the implementation."),
    H("S5.4 "),
    P("Treating a mediator as a species that merely commutes"), EQ("S12"), EQ("S13"), EQ("S14"), EQ("S15"),
    P("valid in the regimes δ/x_k"), EQ("S16"),
    KEEP("Both diffusivities in those two groups", ["The three rows drawn in main-text Fig. 6d–f"]),
    P("Because x_k shrinks to sub-micrometer scale"),
    KEEP("The solver reproduces the three analytic regimes.", ["The solver reproduces the three analytic regimes.", "As k → 0 the plateau recovers", "At intermediate k the computed plateau", "At larger k still, the system enters"]),
    H("S5.5 "),
    KEEP("Every mediated entry of the 50-reaction set", ["Every mediated entry of the 50-reaction set", "Electron bookkeeping:", "Every specification is checked at runtime", "Ramping the current cannot cross", "The ramp is therefore used only", "All 56 mediated cells reach"]),
    mkTable(["Mediated system", "k (M⁻¹s⁻¹)", "k source", "x_k (μm)", "stirred: Stage-0 → EC′ (mA/cm²)", "ANEC: Stage-0 → EC′", "limiter at i_lim"],
      s6Rows.map(r => [r[0], r[1], "⟦" + refsIn(r[2]).join(",") + "⟧", r[3], r[4], r[5], r[6]]), [2100, 800, 1300, 700, 1500, 1400, 1920]),
    KEEPCAP("Table S6.", ["Table S6.", "The mediated EC\u2032 matrix", "Fitting ln i_lim", "Stage-0 is the commuting bound"]),   // 2026-09-21: the main text cites Table S6 for the log-log slopes; the condensed caption had dropped that sentence
    P("The same content can be read nondimensionally"), EQ("S17"),
    KEEP("with μ = n_c C_med D_med", ["with μ = n_c C_med D_med"]),
    H("S5.6 "), P("Every continuum-model configuration with a tractable"),
    H("S5.7 "),
    KEEP("Mechanistically a molecular catalyst is an EC′ carrier", ["Mechanistically a molecular catalyst is an EC′ carrier", "Credited with no turnover inside the film", "The eight mediated rows carry"]),
    KEEP("For seven of the eleven rows that step has been measured", ["For seven of the eleven rows that step has been measured", "Four nickel rows", "For the isolated complex", "Two cobalt-electrocatalytic", "The Co(salen) aza-Wacker row", "The remaining four rows"]),
    P("The three rows drawn in main-text Fig. 6h"),
    mkTable(catHdr.slice(0, 5), catRowsC.map(r => r.slice(0, 5)), [3.0, 0.9, 0.9, 1.3, 1.6]),
    cap("Catalyst-carried entries: catalyst and substrate concentrations, the adopted rate constant (§S5.7, Table S7j) and the ceiling the matrix publishes at it (the largest of the seven architectures)."),
    H("S6. "), P("The cell-voltage stack is"), EQ("S18"), P("with a representative E₀ = 2.0 V"), EQ("S19"),
    p("The main-text example, 0.1 M Bu₄NBF₄/DMF (κ = 4.76 mS cm⁻¹, Table S7f) across a 5 mm gap at 100 mA cm⁻², gives " + f2(EX_ECELL) + " V, of which " + f2(EX_OHMIC) + " V is ohmic, " + f2(EX_Q) + " W cm⁻² of heat and a passive steady state of " + EX_TSS.toFixed(0) + " °C in the 100 mL beaker of §S6.1."),
    H("S6.1 "),
    p("We close a lumped energy balance on a representative 100 mL cell with 10 cm² electrodes. " + pick(P("To answer whether cells actually reach solvent boil-off").__t, ["The dissipated overpotential heat per electrode area"], "S6.1 opening")),
    EQ("S20"), EQ("S21"), EQ("S22"),
    KEEP("where U′ = UA/A_elec is the heat-rejection coefficient", ["where U′ = UA/A_elec", "The passive coefficient is derived", "Treating the internal and external films", "For the 100 mL beaker, σ is"]),
    p("For the compact cells σ is ≈7 for the microfluidic chip and ≈0.8 for an interior cell of a zero-gap stack; the two flow cells and the two rotating electrodes take the beaker value, and each value is given with its package geometry in Table S7i."),
    p("Each architecture is evaluated at its own median limiting current from Table S5."),
    KEEP("This section separates the variables that decide whether a cell boils", ["Fixing the reactor", "At the two rotating archetypes", "The zero-gap stack fails in all four", "The microfluidic cell clears all four"]),
    H("S6.2 "),
    p("Setting T_ss to the boiling point at each architecture's transport ceiling gives the required heat-rejection coefficient, U′_req = q(i_design)/(T_b − T_amb), which is compared with the three cooling classes of Table S7i and with the passive coefficient of each cell. " + pick(P("Where a cell does fall short the design question").__t, ["Where passive rejection falls short"], "S6.2")),
    H("S6.3 "),
    KEEP("The analysis above uses the 25 °C conductivities", ["The analysis above uses the 25 °C conductivities", "Conductivity rises with temperature"]),
    p("We bracket the effect: the lower end is κ fixed at 25 °C, the value used throughout §S6; the upper end is Arrhenius scaling of κ from 25 °C to the boiling point with an activation energy of 15 kJ mol⁻¹ (Table S7i)."),
    KEEP("Applied at each solvent's boiling point", ["Applied at each solvent's boiling point", "The unstirred-beaker ceilings of §S6.1 then move"]),
    H("S6.4 "),
    KEEP("Two terms in the heat balance carry no source", ["Two terms in the heat balance carry no source", "Each is swept and reported as a breaking point"]),
    H("S7. "),
    KEEP("The full matrix applies the same physical model", ["The full matrix applies the same physical model", "All 350 cells are converged solutions"]),
    T("Reactor archetype | median"), KEEPCAP("Table S5.", ["Table S5.", "Results across the 50-reaction set"]),
    KEEP("These thresholds are anchored in the pharmaceutical-industry survey", ["These thresholds are anchored"]),
    H("S8. "),
    KEEP("The parameter table quantifies the data problem", ["The parameter table quantifies the data problem"]),
    p("The resulting bounds on the reported quantities are given in §S10 (Tables S8 and S9), and the extrapolation of the rotating-cylinder correlation in §S3.3."),
    H("S8.1 "),
    p("Productivity and pumping cost are computed for a pair of laminar parallel-plate channels, 1 mm / 5 cm / 5 cm s⁻¹ and 250 µm / 2.5 cm / 10 cm s⁻¹ (gap / length / mean velocity; Table S7g). " + pick(P("A limiting current density is a flux").__t, ["Residence time is τ = L/u", "At the median carrier diffusivity"], "S8.1")),
    KEEP("Comparing the 1 mm and 250 µm channels", ["The thinner gap lowers δ", "Although the residence time decreases", "The tradeoff is pumping"]),
    H("S9. "),
    KEEP("Table S7 groups every model parameter by category", ["Table S7 groups every model parameter", "Measured values are tied to", "Derived values are calculated", "Assumed values are used only"]),
    H("S9.0 "),
    KEEP("Each row of Table S7 carries an Equation column", ["Each row of Table S7 carries an Equation column"]),
    EQ("S23"), KEEP("Le Bas additive molar volume", ["Le Bas additive molar volume", "Increments v_i and the ring corrections"]),
    EQ("S24"), KEEP("Stokes–Einstein, used for the eleven", ["Stokes–Einstein, used for the eleven"]),
    EQ("S25"), P("Nernst–Einstein, used for the five small-ion carriers"),
    EQ("S26"), P("Casteel–Amis."),
    EQ("S27"), EQ("S28"), KEEP("Kohlrausch additivity and the ceiling it implies.", ["Kohlrausch additivity and the ceiling it implies."]),
    EQ("S29"), KEEP("The Debye–Hückel–Onsager limiting law", ["The Debye–Hückel–Onsager limiting law"]),
    EQ("S30"), P("Perkins–Geankoplis mole-fraction rule"), EQ("S31"), P("Kinematic viscosity, which enters the Schmidt number"),
    EQ("S32"), EQ("S33"), KEEP("Surrogate-anchored diffusivity", ["Surrogate-anchored diffusivity", "Eq. S32 is Eq. S2 written for two solutes"]),
    ...S7C,
    H("S10. "),
    KEEP("Each quantity reported in the main text is given below", ["Each quantity reported in the main text is given below", "The model is re-evaluated at those limits"]),
    T("Reported quantity", 0), KEEPCAP("Table S8.", ["Table S8.", "Bounds on the transport quantities", "Medians in mA cm"]),
    T("Reported quantity", 1), KEEPCAP("Table S9.", ["Table S9.", "Bounds on the thermal quantities", "Ceilings and zero-gap currents", "Rows marked one-sided"]),
    ...sec11,
  ];

  // ---- references: renumbered by first appearance in the condensed document ----
  const order = [];
  [...DOC_FRONT, ...DOC_TABLES2, ...DOC_BACK].forEach(el => [el.__t, el.__cells].forEach(s => { if (s) refsIn(s).forEach(k => { if (!order.includes(k)) order.push(k); }); }));
  const REFKEYS = REFS.map(r => r.k);
  order.forEach(k => { if (!REFKEYS.includes(k)) throw new Error("condensed SI cites unknown reference " + k); });
  if (!process.env.SI_REFORDER) {
    const tmp = path.join(require("os").tmpdir(), "si_condensed_reforder_" + process.pid + ".json");
    fs.writeFileSync(tmp, JSON.stringify(order));
    require("child_process").execFileSync(process.execPath, [__filename], { env: { ...process.env, SI_REFORDER: tmp }, stdio: "inherit" });
    fs.unlinkSync(tmp);
    process.exit(0);
  }
  const want = JSON.parse(fs.readFileSync(process.env.SI_REFORDER, "utf8"));
  if (JSON.stringify(want) !== JSON.stringify(order))
    throw new Error("condensed SI: first-appearance order changed between passes");
  DOC_BACK.push(h1("References"),
    ...order.map((k, i) => new Paragraph({
      children: [new TextRun({ text: (i + 1) + "  ", size: 18, font: "Calibri" }),
                 ...REFS.find(r => r.k === k).s.map(sg => new TextRun({ text: sg.t, size: 18, font: "Calibri", italics: !!sg.i, bold: !!sg.b }))],
      spacing: { after: 40 }, indent: { left: 420, hanging: 420 } })));
  console.log("condensed SI: " + order.length + " of " + REFS.length + " references cited, renumbered by first appearance; "
    + (DOC_FRONT.length + DOC_TABLES2.length + DOC_BACK.length) + " elements");
}

const doc = new Document({
  styles: { default: { document: { run: { font: "Calibri", size: 20 } } } },
  sections: [
    { properties: { page: { ...letter, margin: { top: 1080, bottom: 1080, left: 1260, right: 1260 } } }, children: DOC_FRONT },
    { properties: { page: { size: { width: 12240, height: 15840, orientation: PageOrientation.LANDSCAPE }, margin: { top: 720, bottom: 720, left: 900, right: 900 } } }, children: DOC_TABLES2 },
    { properties: { page: { ...letter, margin: { top: 1080, bottom: 1080, left: 1260, right: 1260 } } }, children: DOC_BACK },
  ],
});

Packer.toBuffer(doc).then(b => {
  fs.writeFileSync(OUT_DOCX, b);
  console.log("docx written -> " + OUT_DOCX);
  if (TABLE_DRIFT.length) {
  console.log("TABLE DRIFT corrected from the CSVs (" + TABLE_DRIFT.length + "):");
  TABLE_DRIFT.forEach(d => console.log("   " + d));
} else { console.log("Tables S3/S4: every typed number already matched the registry"); }
console.log("registry census: " + CENSUS_ALL.n + " parameters (" + CENSUS_ALL.measured + " measured, " +
              CENSUS_ALL.derived + " derived, " + CENSUS_ALL.assumption + " assumption); conductivities " +
              CENSUS_COND.n + " (" + CENSUS_COND.measured + "/" + CENSUS_COND.derived + "/" +
              CENSUS_COND.assumption + "), solver diffusivities " + CENSUS_DIFF.n +
              " (" + CENSUS_DIFF.assumption + " assumption)");
});
