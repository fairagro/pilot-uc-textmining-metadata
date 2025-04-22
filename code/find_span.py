def find_text_span(text, span):
    start = text.find(span)
    if start == -1:
        return None  # Span not found
    end = start + len(span)
    return (start, end)

# Example usage:
text = "The long-term field trial started 1992 in Bernburg, Saxony-Anhalt, Germany (51°82' N, 11°70', 138 m above sea level). The soil is a loess chernozem over limestone with an effective rooting depth of 100 cm, containing 22% clay, 70% silt and 8% sand in the ploughed upper (Ap) horizon. It has a neutral pH (7.0–7.4) and an appropriate P and K supply (45–70 mg kg-1 and 130–185 mg kg-1 in calcium-acetate-lactate extract, respectively). The 1980–2010 annual average temperature was 9.7°C, and the average annual precipitation was 511 mm. On five large parcels in strip split plot design (1.2 ha each, main plots) the individual crops grain maize (Zea mays), winter wheat (Triticum aestivum), winter barley (Hordeum vulgare), winter rapeseed (Brassica napus ssp. napus), and winter wheat are rotated on the main plots and grown in parallel. All crop residues remain on the fields. Conservation tillage with a cultivator (CT; 10 cm flat non-inversion soil loosening) is compared to sub-plots with conventional tillage (MP; mould-board plough, carrier board with combined alternating ploughshares, ploughing depth 30 cm, incl. soil inversion). The differentially managed soils are either intensively (Int) operated according to usual practice regarding N supply and pesticide application or extensively managed (Ext) with reduced N supply, without fungicides, and growth regulators. The climate data are not included in the data set. They can be downloaded via the DWD's Open Data Server because there is a DWD weather station (ID 00445) in Bernburg-Strenzfeld. Description of table 1 Related datasets are listed in the metadata element 'Related Identifier'. Dataset version 1.0"
span = "grain maize"
position = find_text_span(text, span)
print(position)  # Output: (10, 19)
