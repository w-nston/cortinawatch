// ---------------------------------------------------------------------------
//  All tour copy lives here. Edit this file to change text, order or exhibits.
//  Source: https://www.cortinawatch.com/en/patek-philippe/patek-philippe-cortina-watch/
//
//  Each chapter is one stop ("bay") in the gallery.
//    side     -1 = left wall, 1 = right wall, 0 = centre of the hall
//    exhibit  which 3D exhibit to build (see js/exhibits.js)
//    wall     the large lettering on the wall behind the exhibit
//    details  optional key/value list shown under the text
//    inspect  true = visitors can click the exhibit to rotate it up close
//    image    optional photograph { src, alt, w, h } (images: several), from the Cortina Watch
//             page, saved in assets/cortina/
// ---------------------------------------------------------------------------

export const site = {
  title: 'Patek Philippe & Cortina Watch',
  ctaLabel: 'Visit a Patek Philippe boutique',
  ctaHref: 'https://www.cortinawatch.com/en/patek-philippe/patek-philippe-cortina-watch/',
  // Watches in the gallery show the current time in Singapore.
  timeZoneOffsetHours: 8,
};

export const chapters = [
  {
    id: 'welcome',
    nav: 'Welcome',
    side: 0,
    exhibit: 'arch',
    kicker: 'An appreciation',
    title: 'Patek Philippe & Cortina Watch',
    body: 'A friendship spanning seven decades and three generations of two families. Scroll to walk through the gallery.',
  },
  {
    id: '1956',
    image: { src: 'assets/cortina/Patek-x-CW-Page_Hero-Image.webp', alt: 'Two gentlemen of the Stern and Lim families looking through a book together', w: 1332, h: 751 },
    nav: '1956',
    side: -1,
    exhibit: 'meeting',
    wall: { big: '1956', small: 'The meeting' },
    kicker: '1956',
    title: 'Where it began',
    body: 'The story begins in 1956, when Mr. Anthony Lim met the Stern family of Patek Philippe. It was the start of a friendship that would carry both families through every change the watch world had to come.',
  },
  {
    id: '1978',
    image: { src: 'assets/cortina/Patek-x-CW-Page_The-First-Patek-Philippe-Authorized-Retailer.webp', alt: 'An early Cortina Watch shop front, its windows full of watches', w: 1116, h: 629 },
    nav: '1972 – 1978',
    side: 1,
    exhibit: 'calatrava',
    wall: { big: '1978', small: 'First authorized retailer in Singapore' },
    kicker: '1972 – 1978',
    title: 'The first authorized retailer',
    body: 'As the 1970s shook the Swiss mechanical watch industry, the Stern family deepened their commitment to mechanical calibres. Mr. Anthony Lim shared that conviction: he founded Cortina Watch in 1972, and in 1978 Cortina became the first authorized retailer of Patek Philippe in Singapore.',
  },
  {
    id: '1980s',
    image: { src: 'assets/cortina/Patek-x-CW-Page_A-Time-of-Perseverance-and-Strategic-Planning.webp', alt: 'Two men in suits in front of a “Museum Pieces” display', w: 1440, h: 648 },
    nav: '1980s',
    side: -1,
    exhibit: 'balance',
    wall: { big: '1980s', small: 'Perseverance' },
    kicker: '1980s',
    title: 'A time of perseverance',
    body: 'Through the economic disruption and market corrections of the 1980s, the relationship carried both families forward, with patience and strategic planning kept steady like the balance wheel at the heart of every mechanical watch.',
  },
  {
    id: '5057r',
    image: { src: 'assets/cortina/Patek-x-CW-Page_A-Testimony-in-the-Form-of-a-Timepiece.webp', alt: 'The rose gold Ref. 5057R beside its attestation of limited edition', w: 1400, h: 648 },
    nav: '1997 · 5057R',
    side: 1,
    exhibit: 'watch5057R',
    inspect: true,
    wall: { big: '1997', small: 'The Cortina Jubilee' },
    kicker: '1997 · 25th Jubilee',
    title: 'Ref. 5057R',
    body: 'For Cortina Watch’s 25th Jubilee, Mr. Philippe Stern proposed a Ref. 5057 as an anniversary piece: a testimony to the friendship in the form of a timepiece.',
    details: [
      ['Reference', '5057R'],
      ['Case', '18K rose gold, hobnail bezel'],
      ['Dial', 'White, Roman numerals'],
      ['Functions', 'Power reserve, pointer date, moon phase, small seconds'],
      ['Edition', 'Limited to 100 pieces'],
    ],
  },
  {
    id: '2000s',
    image: { src: 'assets/cortina/Patek-x-CW-Page_Exclusive-Boutique-Concept.webp', alt: 'Four men in front of a Patek Philippe backdrop', w: 1116, h: 629 },
    nav: '2000s',
    side: -1,
    exhibit: 'shops',
    wall: { big: '2000s', small: 'The boutique concept' },
    kicker: '2000s',
    title: 'The boutique concept',
    body: 'Mr. Raymond Lim, Mr. Anthony Lim’s eldest son, pioneered the shop-in-shop concept at Paragon, Raffles City and Millenia Walk, laying the groundwork for stand-alone Patek Philippe boutiques in Singapore.',
  },
  {
    id: '2010',
    image: { src: 'assets/cortina/Patek-x-CW-Page_Opening-of-the-Patek-Philippe-Boutique.webp', alt: 'The front of a Patek Philippe boutique', w: 1440, h: 648 },
    nav: '2010',
    side: 1,
    exhibit: 'marinaBay',
    wall: { big: '2010', small: 'Marina Bay Sands' },
    kicker: '2010',
    title: 'A boutique by the bay',
    body: 'During the global financial crisis, the next generation, Mr. Thierry Stern and Mr. Jeremy Lim, discussed opening a Patek Philippe boutique at The Shoppes at Marina Bay Sands. It went ahead in 2010.',
  },
  {
    id: '2015',
    image: { src: 'assets/cortina/Patek-x-CW-Page_A-Watch-Speaks-Louder-Than-Words.webp', alt: 'A watch presented in its box in a Patek Philippe salon', w: 1116, h: 629 },
    nav: '2015',
    side: -1,
    exhibit: 'calatrava5227',
    inspect: true,
    wall: { big: '2015', small: 'A watch speaks louder than words' },
    kicker: '2015',
    title: 'A gift for an 80th birthday',
    body: 'Mr. Philippe Stern travelled to Singapore for Mr. Anthony Lim’s 80th birthday with a white gold Calatrava Ref. 5227, its caseback engraved “Happy 80th Birthday, Philippe et Thierry Stern”. Inspect the watch to see the caseback.',
    details: [
      ['Reference', 'Calatrava 5227'],
      ['Case', 'White gold'],
      ['Caseback', '“Happy 80th Birthday, Philippe et Thierry Stern”'],
    ],
  },
  {
    id: '2016',
    image: { src: 'assets/cortina/Patek-x-CW-Page_Expansion-of-Footprint-in-Asia.webp', alt: 'The ribbon cut at the opening of a Patek Philippe boutique', w: 1116, h: 629 },
    nav: '2016',
    side: 1,
    exhibit: 'salon',
    wall: { big: '2016', small: 'ION Orchard' },
    kicker: '2016',
    title: 'Singapore’s Geneva salon',
    body: 'With six specialist Patek Philippe boutiques across the region, Cortina facilitated the expansion of the Patek Philippe boutique at ION Orchard, the largest in Southeast Asia, with private rooms and VIP lounges described as Singapore’s answer to the famed Geneva salon.',
  },
  {
    id: '5057g',
    image: { src: 'assets/cortina/Patek-x-CW-Page_A-Special-Commemoration.webp', alt: 'The enamel Dome Clock and the Ref. 5057G beside the Cortina Watch 50 emblem', w: 1116, h: 629 },
    nav: '50 years · 5057G',
    side: -1,
    exhibit: 'watch5057G',
    inspect: true,
    feature: true,
    wall: { big: '50', small: 'Cortina Watch · since 1972' },
    kicker: '50th anniversary',
    title: 'Ref. 5057G · The Cortina',
    body: 'Twenty-five years after the first Jubilee watch, the partners marked Cortina Watch’s 50th anniversary with a new limited edition based on the 1997 model, reinterpreted in a contemporary design.',
    details: [
      ['Reference', '5057G'],
      ['Case', 'White gold, hobnail bezel'],
      ['Dial', 'Slate grey sunburst, Roman numerals'],
      ['Functions', 'Power reserve, pointer date, moon phase, small seconds'],
      ['Inspired by', 'The 1997 Ref. 5057R'],
    ],
  },
  {
    id: 'dome',
    nav: 'Dome Clock',
    side: 1,
    exhibit: 'dome',
    inspect: true,
    wall: { big: '50', small: 'Colours of enamel' },
    kicker: '50th anniversary',
    title: 'The Dome Clock',
    body: 'Patek Philippe also presented a Dome Clock depicting Singapore’s urban landscape in 50 enamel colours, with fireworks bursting across the dome.',
  },
  {
    id: 'craft',
    nav: 'The craft',
    side: -1,
    exhibit: 'movement',
    wall: { big: 'Geneva', small: 'Plan-les-Ouates' },
    kicker: 'The craft',
    title: 'Born in Plan-les-Ouates',
    body: 'Every chapter of this story rests on the mechanical masterpieces made at the Patek Philippe manufacture in Plan-les-Ouates, Geneva. As you approach, the movement opens up, part by part.',
  },
  {
    id: 'future',
    images: [
      { src: 'assets/cortina/Patek-Philippe_Starhill-KL_Cortina-Watch-1.webp', alt: 'The Patek Philippe boutique at The Starhill, Kuala Lumpur', w: 2232, h: 1258 },
      { src: 'assets/cortina/Patek-Philippe_One-Bangkok_Cortina-Watch.webp', alt: 'The Patek Philippe boutique at One Bangkok', w: 1440, h: 648 },
    ],
    nav: 'The future',
    side: 1,
    exhibit: 'map',
    wall: { big: 'Next', small: 'Looking to the future' },
    kicker: 'Looking to the future',
    title: 'Across Southeast Asia',
    body: 'The partnership continues beyond Singapore, with Patek Philippe boutiques at The Starhill in Kuala Lumpur and at One Bangkok, the manufacture’s first duplex boutique in Southeast Asia.',
  },
  {
    id: 'seven-decades',
    image: { src: 'assets/cortina/Patek-x-CW-Page_Six-Decades-and-Counting.webp', alt: 'Four men of the two families in a Patek Philippe boutique', w: 1440, h: 648 },
    nav: 'Seven decades',
    side: 0,
    exhibit: 'finale',
    kicker: 'Seven decades and counting',
    title: 'Three generations. One friendship.',
    body: 'From 1956 to today, the Lim and Stern families have shared one belief: in the enduring value of the mechanical watch.',
    cta: true,
  },
];

// ---------------------------------------------------------------------------
//  The two anniversary watches shown in the exhibition's vitrine (index.html).
//  model: the GLB in assets/models/. Facts: Cortina Watch, Phillips, Sotheby's
//  and WatchesBySJX listings; the movement details are the watches' own (the
//  22K rotor and TWENTY-NINE JEWELS are engraved on them).
// ---------------------------------------------------------------------------
export const watches = [
  {
    id: '5057r',
    image: { src: 'assets/cortina/Patek-x-CW-Page_A-Testimony-in-the-Form-of-a-Timepiece.webp', alt: 'The rose gold Ref. 5057R beside its attestation of limited edition', w: 1400, h: 648 },
    model: 'assets/models/5057R.glb',
    year: '1997',
    label: 'Ref. 5057R',
    kicker: '1997 · The Cortina Jubilee',
    title: 'Ref. 5057R',
    history: [
      'In 1997 Cortina Watch turned twenty-five. To mark the Jubilee, Mr. Philippe Stern proposed a Ref. 5057 as an anniversary piece: a testimony to the friendship between the Stern and Lim families, in the form of a timepiece.',
      'One hundred were made, in 18K rose gold with a white dial, Roman numerals and a hobnail bezel. Through the sapphire caseback, printed “Cortina Jubilee Watch”, turns the self-winding calibre 240 with its 22K gold mini-rotor.',
    ],
    details: [
      ['Edition', '100 pieces'],
      ['Case', '18K rose gold, hobnail bezel'],
      ['Dial', 'White, Roman numerals'],
      ['Indications', 'Power reserve, pointer date, moon phase, small seconds'],
      ['Movement', 'Self-winding calibre 240, 22K gold mini-rotor'],
    ],
  },
  {
    id: '5057g',
    image: { src: 'assets/cortina/Patek-x-CW-Page_A-Special-Commemoration.webp', alt: 'The enamel Dome Clock and the Ref. 5057G beside the Cortina Watch 50 emblem', w: 1116, h: 629 },
    model: 'assets/models/5057G.glb',
    year: '2022',
    label: 'Ref. 5057G',
    kicker: '2022 · Cortina Watch 50th Anniversary',
    title: 'Ref. 5057G',
    history: [
      'Twenty-five years later, for Cortina Watch’s 50th anniversary, Patek Philippe returned to the Jubilee watch. The Ref. 5057G-010 keeps the design and the movement of the 1997 piece, reinterpreted in white gold with a slate-grey sunburst dial and applied Roman numerals.',
      'Again limited to one hundred pieces, it was offered only through Cortina Watch. Its sapphire caseback reads “Cortina Watch · 50th Anniversary · Since 1972”.',
    ],
    details: [
      ['Edition', '100 pieces'],
      ['Case', 'White gold, hobnail bezel'],
      ['Dial', 'Slate-grey sunburst, applied Roman numerals'],
      ['Indications', 'Power reserve, pointer date, moon phase, small seconds'],
      ['Movement', 'Self-winding calibre 240, 22K gold mini-rotor'],
    ],
  },
];
