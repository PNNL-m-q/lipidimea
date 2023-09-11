-- DATABASE SCHEMA FOR DDA-DIA ANALYSIS RESULTS
--
-- -- All non "public-facing" tables are named with prepended _ 


----------- DDA Features --------------

-- table with descriptions for columns in DDAFeatures table
CREATE TABLE _DDAFeatures_COLUMNS (
    col_name TEXT NOT NULL,
    col_desc TEXT NOT NULL
);
INSERT INTO _DDAFeatures_COLUMNS VALUES 
    ('dda_feat_id', 'unique feature identifier'),
    ('f', 'raw data file this lipid was identified in'),
    ('mz', 'precursor m/z'),
    ('rt', 'observed retention time of chromatographic peak'),
    ('rt_fwhm', 'FWHM of chromatographic peak'),
    ('rt_pkht', 'height of chromatographic peak'),
    ('rt_psnr', 'signal to noise ratio for chromatographic peak'),
    ('ms2_n_scans', 'number of MS2 scans for this precursor'),
    ('ms2_n_peaks', 'number of peaks in centroided spectrum'),
    ('ms2_peaks', 'MS2 spectrum (centroided, unannotated) in single line "{mz}:{intensity} {mz}:{intensity} ..." format');

-- table with LC-MS/MS (DDA) features
CREATE TABLE DDAFeatures (
    dda_feat_id INTEGER PRIMARY KEY,
    f TEXT NOT NULL,
    mz REAL NOT NULL,
    rt REAL NOT NULL,
    rt_fwhm REAL NOT NULL,
    rt_pkht REAL NOT NULL,
    rt_psnr REAL NOT NULL,
    ms2_n_scans INT NOT NULL,
    ms2_n_peaks INT,
    ms2_peaks TEXT
);


----------- DIA Features --------------

-- table with descriptions for columns in DIAFeatures table
CREATE TABLE _DIAFeatures_COLUMNS (
    col_name TEXT NOT NULL,
    col_desc TEXT NOT NULL
);
INSERT INTO _DIAFeatures_COLUMNS VALUES 
    ('dia_feat_id', 'unique feature identifier'),
    ('dda_feat_id', 'reference to corresponding feature in DDAFeatures table'),
    ('f', 'raw data file this lipid was identified in'),
    ('mz', 'precursor m/z'),
    ('ms1', 'partial MS1 spectrum (M-1.5 to M+2.5)'),
    ('rt', 'observed retention time of chromatographic peak'),
    ('rt_fwhm', 'FWHM of chromatographic peak'),
    ('rt_pkht', 'height of chromatographic peak'),
    ('rt_psnr', 'signal to noise ratio for chromatographic peak'),
    ('xic', 'raw XIC, numpy.ndarray (as bytes)'),
    ('dt', 'observed arrival time of ATD peak'),
    ('dt_fwhm', 'FWHM of ATD peak'),
    ('dt_pkht', 'height of ATD peak'),
    ('dt_psnr', 'signal to noise ratio for ATD peak'),
    ('atd', 'raw ATD, numpy.ndarray (as bytes)'),
    ('ccs', 'calibrated CCS'),
    ('ms2_n_peaks', 'number of peaks in centroided spectrum'),
    ('ms2_peaks', 'MS2 spectrum (centroided, unannotated) in single line "{mz}:{intensity} {mz}:{intensity} ..." format'),
    ('ms2', 'raw MS2 spectrum, numpy.ndarray (as bytes)'),
    ('decon_frag_ids', 'identifiers for any deconvoluted fragments, separated by spaces');

-- table with LC-IMS-MS/MS (DIA) features
-- this is not the public-facing table for querying the data
-- the DIAFeatures view is used for that
CREATE TABLE _DIAFeatures (
    dia_feat_id INTEGER PRIMARY KEY,
    dda_feat_id INT NOT NULL,
    f TEXT NOT NULL,
    ms1 BLOB,
    rt REAL NOT NULL,
    rt_fwhm REAL NOT NULL,
    rt_pkht REAL NOT NULL,
    rt_psnr REAL NOT NULL,
    xic BLOB,
    dt REAL NOT NULL,
    dt_fwhm REAL NOT NULL,
    dt_pkht REAL NOT NULL,
    dt_psnr REAL NOT NULL,
    atd BLOB,
    ccs REAL,
    ms2_n_peaks INT,
    ms2_peaks TEXT,
    ms2 BLOB
);

-- table with descriptions for columns in DIADeconFragments table
CREATE TABLE _DIADeconFragments_COLUMNS (
    col_name TEXT NOT NULL,
    col_desc TEXT NOT NULL
);
INSERT INTO _DIADeconFragments_COLUMNS VALUES 
    ('decon_frag_id', 'unique fragment identifier'),
    ('', '');

-- table containing data for deconvoluted fragments from DIA features
CREATE TABLE DIADeconFragments (
    decon_frag_id INTEGER PRIMARY KEY,
    mz REAL NOT NULL,
    xic BLOB,
    xic_dist REAL NOT NULL,
    atd BLOB,
    atd_dist REAL NOT NULL
);


-- table for mapping DIA feature IDs to deconvoluted fragment IDs
CREATE TABLE _DIAFeatsToDeconFrags (
    dia_feat_id INTEGER NOT NULL,
    decon_frag_id INTEGER NOT NULL
);


-- view FROM _DIAFeatures table that adds a generated column with deconvoluted fragment IDs
-- this serves as the public-facing table for querying the data
CREATE VIEW DIAFeatures AS 
    SELECT 
        dia_feat_id,
        dda_feat_id,
        dia.f,
        mz,
        ms1,
        dia.rt,
        dia.rt_fwhm,
        dia.rt_pkht,
        dia.rt_psnr,
        xic,
        dt,
        dt_fwhm,
        dt_pkht,
        dt_psnr,
        atd,
        ccs,
        dia.ms2_n_peaks,
        dia.ms2_peaks,
        dia.ms2,
        (
			SELECT 
                frgids 
			FROM (
				SELECT 
					_DIAFeatsToDeconFrags.dia_feat_id AS diaid,  
					group_concat(decon_frag_id, " ") AS frgids 
				FROM 
                    _DIAFeatsToDeconFrags  
				GROUP BY diaid
                ) 
			WHERE 
                diaid=dia_feat_id
		) AS decon_frag_ids
    FROM 
        _DIAFeatures AS dia
        INNER JOIN DDAFeatures USING(dda_feat_id);


----------- Combined Features --------------

CREATE VIEW CombinedFeatures AS 
    SELECT
        dia.dia_feat_id AS dia_feat_id,
        dia.dda_feat_id AS dda_feat_id,
        dia.f AS dia_f,
        dda.f AS dda_f,
        dda.mz AS mz,
        dia.rt AS dia_rt,
        dda.rt AS dda_rt,
        dia.dt AS dt,
        dia.ccs AS ccs,
        dia.ms2_peaks AS dia_ms2_peaks,
        dda.ms2_peaks AS dda_ms2_peaks,
        dia.decon_frag_ids AS dia_decon_frag_ids,
        dia.xic AS dia_xic,
        dia.atd AS dia_atd,
        dia.ms1 AS dia_ms1,
        dia.ms2 AS dia_ms2,
        dda.rt_fwhm AS dda_rt_fwhm,
        dda.rt_pkht AS dda_rt_pkht,
        dda.rt_psnr AS dda_rt_psnr,
        dia.rt_fwhm AS dia_rt_fwhm,
        dia.rt_pkht AS dia_rt_pkht,
        dia.rt_psnr AS dia_rt_psnr,
        dia.dt_fwhm AS dia_dt_fwhm,
        dia.dt_pkht AS dia_dt_pkht,
        dia.dt_psnr AS dia_dt_psnr,
        dda.ms2_n_scans AS dda_ms2_n_scans,
        dda.ms2_n_peaks AS dda_ms2_n_peaks,
        dia.ms2_n_peaks AS dia_ms2_n_peaks
    FROM
        DIAFeatures AS dia 
        INNER JOIN DDAFeatures AS dda USING(dda_feat_id);


----------- Lipid Annotations --------------

-- table with descriptions for columns in Lipids table
CREATE TABLE _Lipids_COLUMNS (
    col_name TEXT NOT NULL,
    col_desc TEXT NOT NULL
);
INSERT INTO _Lipids_COLUMNS VALUES 
    ('ann_id', 'unique annotation identifier'),
    ('dia_feat_id', 'reference to feature identifier from DIAFeatures table'),
    ('lipid', 'lipid annotation, made at the level of sum composition or higher if supporting fragment(s) found in MS2 spectrum'),
    ('adduct', 'MS adduct/ionization state'),
    ('ppm', 'mass error in ppm relative to theoretical monoisotopic mass'),
    ('ccs_rel_err', 'relative CCS error in percent')
    ('fragments', 'annotated peaks from MS2 spectrum in single line "{label}_{mz} {label}_{mz} ..." format');

-- table with Lipid annotations
CREATE TABLE Lipids (
    ann_id INTEGER PRIMARY KEY,
    dia_feat_id INT NOT NULL,
    lipid TEXT NOT NULL,
    adduct TEXT NOT NULL,
    ppm REAL NOT NULL,
    ccs_rel_err REAL,
    fragments TEXT
);
