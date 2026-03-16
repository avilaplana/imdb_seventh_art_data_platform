SELECT
    tl.title_id,
    tl.title as localized_title
    tl.is_original_title,
    tl.localized_title,    
    r.region_name,
    l.language_name    
FROM {{ ref('title_localized') }} tl
JOIN {{ ref('regions') }} tr ON tl.region_id = tr.region_id
JOIN {{ ref('languages') }} l ON tl.language_id = l.language_id
