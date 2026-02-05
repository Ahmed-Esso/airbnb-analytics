-- #1 ListingScore (JOIN benchmark + computed features) join1
WITH base AS (
    SELECT
        l.city,
        l.country,
        r.room_type,
        r.room_shared,
        r.room_private,
        f.realSum,
        f.cleanliness_rating,
        f.guest_satisfaction_overall,
        f.person_capacity,
        f.bedrooms,
        f.dist,
        f.metro_dist,
        d.is_weekend,
        h.host_is_superhost,
        a.wifi, a.kitchen, a.air_conditioning, a.parking, a.tv, a.heating
    FROM dbo.Fact_Listings f
    JOIN dbo.Dim_Location  l ON l.location_sk  = f.location_sk
    JOIN dbo.Dim_Room_Type r ON r.room_type_sk = f.room_type_sk
    JOIN dbo.Dim_Day       d ON d.day_sk       = f.day_sk
    JOIN dbo.Dim_Host      h ON h.host_sk      = f.host_sk
    JOIN dbo.Dim_Amenities a ON a.amenity_sk   = f.amenity_sk
    WHERE f.realSum IS NOT NULL
),
bench AS (
    SELECT
        city,
        room_type,
        AVG(realSum) AS bench_avg,
        COUNT(*) AS bench_n
    FROM base
    GROUP BY city, room_type
),
listing AS (
    SELECT
        b.*,
        (CAST(wifi AS INT)+CAST(kitchen AS INT)+CAST(air_conditioning AS INT)
         +CAST(parking AS INT)+CAST(tv AS INT)+CAST(heating AS INT)) AS amenity_count,
        CASE
            WHEN dist < 1 THEN '0–1 km'
            WHEN dist < 3 THEN '1–3 km'
            WHEN dist < 6 THEN '3–6 km'
            ELSE '6+ km'
        END AS dist_bucket,
        CASE
            WHEN metro_dist < 0.5 THEN '0–0.5 km'
            WHEN metro_dist < 1 THEN '0.5–1 km'
            WHEN metro_dist < 2 THEN '1–2 km'
            ELSE '2+ km'
        END AS metro_bucket
    FROM base b
),
scored AS (
    SELECT
        l.city,
        l.country,
        l.room_type,
        l.realSum,
        bn.bench_avg,
        bn.bench_n,
        (l.realSum - bn.bench_avg) AS diff_amount,
        100.0 * (l.realSum - bn.bench_avg) / NULLIF(bn.bench_avg, 0) AS diff_percent,
        l.cleanliness_rating,
        l.guest_satisfaction_overall,
        l.person_capacity,
        l.bedrooms,
        l.dist,
        l.metro_dist,
        l.dist_bucket,
        l.metro_bucket,
        l.is_weekend,
        l.host_is_superhost,
        l.amenity_count,
        CASE
            WHEN l.guest_satisfaction_overall >= 95 THEN '95–100'
            WHEN l.guest_satisfaction_overall >= 90 THEN '90–94'
            WHEN l.guest_satisfaction_overall >= 80 THEN '80–89'
            ELSE '<80'
        END AS satisfaction_bucket
    FROM listing l
    JOIN bench bn
      ON bn.city = l.city AND bn.room_type = l.room_type
    WHERE bn.bench_n >= 50
)
SELECT TOP (200) *
FROM scored
ORDER BY diff_percent DESC;
GO




-- #2 SegmentDashboard (JOIN scored -> aggregate by segments) join 2
;WITH base AS (
    SELECT
        l.country,
        l.city,
        r.room_type,
        d.is_weekend,
        f.realSum,
        f.cleanliness_rating,
        f.guest_satisfaction_overall,
        f.dist,
        f.metro_dist,
        a.wifi, a.kitchen, a.air_conditioning, a.parking, a.tv, a.heating
    FROM dbo.Fact_Listings f
    JOIN dbo.Dim_Location  l ON l.location_sk  = f.location_sk
    JOIN dbo.Dim_Room_Type r ON r.room_type_sk = f.room_type_sk
    JOIN dbo.Dim_Day       d ON d.day_sk       = f.day_sk
    JOIN dbo.Dim_Amenities a ON a.amenity_sk   = f.amenity_sk
    WHERE f.realSum IS NOT NULL
),
bench AS (
    SELECT city, room_type, AVG(realSum) AS bench_avg, COUNT(*) AS bench_n
    FROM base
    GROUP BY city, room_type
),
scored AS (
    SELECT
        b.country,
        b.city,
        b.room_type,
        b.is_weekend,
        CASE
            WHEN b.dist < 1 THEN '0–1 km'
            WHEN b.dist < 3 THEN '1–3 km'
            WHEN b.dist < 6 THEN '3–6 km'
            ELSE '6+ km'
        END AS dist_bucket,
        CASE
            WHEN b.metro_dist < 0.5 THEN '0–0.5 km'
            WHEN b.metro_dist < 1 THEN '0.5–1 km'
            WHEN b.metro_dist < 2 THEN '1–2 km'
            ELSE '2+ km'
        END AS metro_bucket,
        b.realSum,
        b.cleanliness_rating,
        b.guest_satisfaction_overall,
        (CAST(b.wifi AS INT)+CAST(b.kitchen AS INT)+CAST(b.air_conditioning AS INT)
         +CAST(b.parking AS INT)+CAST(b.tv AS INT)+CAST(b.heating AS INT)) AS amenity_count,
        bn.bench_avg,
        bn.bench_n,
        100.0 * (b.realSum - bn.bench_avg) / NULLIF(bn.bench_avg, 0) AS diff_percent
    FROM base b
    JOIN bench bn
      ON bn.city = b.city AND bn.room_type = b.room_type
    WHERE bn.bench_n >= 50
)
SELECT
    country,
    city,
    room_type,
    dist_bucket,
    metro_bucket,
    is_weekend,
    COUNT(*) AS n,
    AVG(realSum) AS avg_price,
    AVG(diff_percent) AS avg_vs_benchmark_percent,
    AVG(cleanliness_rating) AS avg_clean,
    AVG(guest_satisfaction_overall) AS avg_satisfaction,
    AVG(amenity_count) AS avg_amenities
FROM scored
GROUP BY country, city, room_type, dist_bucket, metro_bucket, is_weekend
HAVING COUNT(*) >= 50
ORDER BY avg_vs_benchmark_percent DESC, avg_price DESC;
GO






-- #3 BestDealsWorstDeals_usingTable (join 3) pricing*

WITH base AS (
    SELECT
        l.city, l.country, r.room_type,
        f.realSum, f.cleanliness_rating, f.guest_satisfaction_overall,
        a.wifi, a.kitchen, a.air_conditioning, a.parking, a.tv, a.heating
    FROM dbo.Fact_Listings f
    JOIN dbo.Dim_Location  l ON l.location_sk  = f.location_sk
    JOIN dbo.Dim_Room_Type r ON r.room_type_sk = f.room_type_sk
    JOIN dbo.Dim_Amenities a ON a.amenity_sk   = f.amenity_sk
    WHERE f.realSum IS NOT NULL
),
bench AS (
    SELECT city, room_type, AVG(realSum) AS bench_avg, COUNT(*) AS bench_n
    FROM base
    GROUP BY city, room_type
),
scored AS (
    SELECT
        b.city, b.country, b.room_type,
        b.realSum,
        bn.bench_avg,
        bn.bench_n,
        (b.realSum - bn.bench_avg) AS diff_amount,
        100.0 * (b.realSum - bn.bench_avg) / NULLIF(bn.bench_avg, 0) AS diff_percent,
        b.cleanliness_rating,
        b.guest_satisfaction_overall,
        (CAST(b.wifi AS INT)+CAST(b.kitchen AS INT)+CAST(b.air_conditioning AS INT)
         +CAST(b.parking AS INT)+CAST(b.tv AS INT)+CAST(b.heating AS INT)) AS amenity_count
    FROM base b
    JOIN bench bn ON bn.city=b.city AND bn.room_type=b.room_type
    WHERE bn.bench_n >= 50
)
SELECT TOP (30)
    'UNDERPRICED' AS label,
    city, country, room_type,
    realSum, bench_avg, diff_amount, diff_percent,
    cleanliness_rating, guest_satisfaction_overall, amenity_count
FROM scored
WHERE cleanliness_rating >= 4.5
  AND guest_satisfaction_overall >= 90
ORDER BY diff_percent ASC;
GO








-- OVERPRICED


WITH base AS (
    SELECT
        l.city, l.country, r.room_type,
        f.realSum, f.cleanliness_rating, f.guest_satisfaction_overall,
        a.wifi, a.kitchen, a.air_conditioning, a.parking, a.tv, a.heating
    FROM dbo.Fact_Listings f
    JOIN dbo.Dim_Location  l ON l.location_sk  = f.location_sk
    JOIN dbo.Dim_Room_Type r ON r.room_type_sk = f.room_type_sk
    JOIN dbo.Dim_Amenities a ON a.amenity_sk   = f.amenity_sk
    WHERE f.realSum IS NOT NULL
),
bench AS (
    SELECT city, room_type, AVG(realSum) AS bench_avg, COUNT(*) AS bench_n
    FROM base
    GROUP BY city, room_type
),
scored AS (
    SELECT
        b.city, b.country, b.room_type,
        b.realSum,
        bn.bench_avg,
        bn.bench_n,
        (b.realSum - bn.bench_avg) AS diff_amount,
        100.0 * (b.realSum - bn.bench_avg) / NULLIF(bn.bench_avg, 0) AS diff_percent,
        b.cleanliness_rating,
        b.guest_satisfaction_overall,
        (CAST(b.wifi AS INT)+CAST(b.kitchen AS INT)+CAST(b.air_conditioning AS INT)
         +CAST(b.parking AS INT)+CAST(b.tv AS INT)+CAST(b.heating AS INT)) AS amenity_count
    FROM base b
    JOIN bench bn ON bn.city=b.city AND bn.room_type=b.room_type
    WHERE bn.bench_n >= 50
)
SELECT TOP (30)
    'OVERPRICED' AS label,
    city, country, room_type,
    realSum, bench_avg, diff_amount, diff_percent,
    cleanliness_rating, guest_satisfaction_overall, amenity_count
FROM scored
ORDER BY diff_percent DESC;
GO




-- #AccessibilitySegment (Metro vs Center) METROOOOOOOOOOOOOO
SELECT
  l.city, l.country,
  r.room_type,
  f.realSum,
  f.dist,
  f.metro_dist,
  f.cleanliness_rating,
  f.guest_satisfaction_overall,
  d.is_weekend,
  h.host_is_superhost,
  CASE
    WHEN f.metro_dist <= 0.5 THEN 'METRO_ADVANTAGE'
    WHEN f.dist <= 1.0 THEN 'CENTER_ADVANTAGE'
    ELSE 'REMOTE'
  END AS accessibility_segment
FROM dbo.Fact_Listings f
JOIN dbo.Dim_Location  l ON l.location_sk  = f.location_sk
JOIN dbo.Dim_Room_Type r ON r.room_type_sk = f.room_type_sk
JOIN dbo.Dim_Day       d ON d.day_sk       = f.day_sk
JOIN dbo.Dim_Host      h ON h.host_sk      = f.host_sk
WHERE f.realSum IS NOT NULL;
GO


-- #AmenityTier (BASIC / COMFORT / FULL)

SELECT
    l.city, l.country,
    r.room_type,
    f.realSum,
    f.cleanliness_rating,
    f.guest_satisfaction_overall,
    (CAST(a.wifi AS INT)+CAST(a.kitchen AS INT)+CAST(a.air_conditioning AS INT)
     +CAST(a.parking AS INT)+CAST(a.tv AS INT)+CAST(a.heating AS INT)) AS amenity_count,
    CASE
        WHEN (CAST(a.wifi AS INT)+CAST(a.kitchen AS INT)+CAST(a.air_conditioning AS INT)
              +CAST(a.parking AS INT)+CAST(a.tv AS INT)+CAST(a.heating AS INT)) <= 1 THEN 'BASIC'
        WHEN (CAST(a.wifi AS INT)+CAST(a.kitchen AS INT)+CAST(a.air_conditioning AS INT)
              +CAST(a.parking AS INT)+CAST(a.tv AS INT)+CAST(a.heating AS INT)) <= 3 THEN 'COMFORT'
        ELSE 'FULL'
    END AS amenity_tier
FROM dbo.Fact_Listings f
JOIN dbo.Dim_Location  l ON l.location_sk  = f.location_sk
JOIN dbo.Dim_Room_Type r ON r.room_type_sk = f.room_type_sk
JOIN dbo.Dim_Amenities a ON a.amenity_sk   = f.amenity_sk
WHERE f.realSum IS NOT NULL;
GO










-- #InsightColumns_AllInOne (ALL)
WITH base AS (
    SELECT
        l.city, l.country, r.room_type,
        f.realSum,
        f.cleanliness_rating,
        f.guest_satisfaction_overall,
        (CAST(a.wifi AS INT)+CAST(a.kitchen AS INT)+CAST(a.air_conditioning AS INT)
         +CAST(a.parking AS INT)+CAST(a.tv AS INT)+CAST(a.heating AS INT)) AS amenity_count
    FROM dbo.Fact_Listings f
    JOIN dbo.Dim_Location  l ON l.location_sk  = f.location_sk
    JOIN dbo.Dim_Room_Type r ON r.room_type_sk = f.room_type_sk
    JOIN dbo.Dim_Amenities a ON a.amenity_sk   = f.amenity_sk
    WHERE f.realSum IS NOT NULL
),
bench AS (
    SELECT city, room_type, AVG(realSum) AS bench_avg, COUNT(*) AS bench_n
    FROM base
    GROUP BY city, room_type
),
scored AS (
    SELECT
        b.*,
        bn.bench_avg,
        bn.bench_n,
        (b.realSum - bn.bench_avg) AS diff_amount,
        100.0 * (b.realSum - bn.bench_avg) / NULLIF(bn.bench_avg, 0) AS diff_percent
    FROM base b
    JOIN bench bn ON bn.city=b.city AND bn.room_type=b.room_type
    WHERE bn.bench_n >= 50
)
SELECT
    city, country, room_type,
    realSum, bench_avg, diff_amount, diff_percent,
    cleanliness_rating, guest_satisfaction_overall, amenity_count,

    CASE
        WHEN diff_percent <= -20 THEN 'UNDERPRICED'
        WHEN diff_percent >=  20 THEN 'OVERPRICED'
        ELSE 'FAIR'
    END AS pricing_status,

    CASE
        WHEN diff_percent <= -20
         AND cleanliness_rating >= 4.5
         AND guest_satisfaction_overall >= 90
          THEN 'GEM'
        WHEN diff_percent >=  20
         AND (cleanliness_rating < 4.2 OR guest_satisfaction_overall < 88)
          THEN 'OVERPRICED_LOW_VALUE'
        ELSE 'FAIR'
    END AS value_segment,

    CASE
        WHEN amenity_count <= 1 THEN 'BASIC'
        WHEN amenity_count <= 3 THEN 'COMFORT'
        ELSE 'FULL'
    END AS amenity_tier

FROM scored
ORDER BY ABS(diff_percent) DESC;
GO

























--#FeatureImpactRadar

WITH base AS (
  SELECT
    l.country, l.city,
    r.room_type, r.room_shared, r.room_private,
    h.host_is_superhost,
    d.day_type, d.is_weekend, d.biz, d.multi,
    a.wifi, a.kitchen, a.air_conditioning, a.parking, a.tv, a.heating,
    (CAST(a.wifi AS INT)+CAST(a.kitchen AS INT)+CAST(a.air_conditioning AS INT)+CAST(a.parking AS INT)+CAST(a.tv AS INT)+CAST(a.heating AS INT)) AS amenity_count,
    f.person_capacity, f.bedrooms, f.beds,
    f.dist, f.metro_dist,
    f.attr_index_norm, f.rest_index_norm,
    f.cleanliness_rating, f.guest_satisfaction_overall,
    f.realSum
  FROM dbo.Fact_Listings f
  JOIN dbo.Dim_Location  l ON l.location_sk  = f.location_sk
  JOIN dbo.Dim_Room_Type r ON r.room_type_sk = f.room_type_sk
  JOIN dbo.Dim_Host      h ON h.host_sk      = f.host_sk
  JOIN dbo.Dim_Day       d ON d.day_sk       = f.day_sk
  JOIN dbo.Dim_Amenities a ON a.amenity_sk   = f.amenity_sk
  WHERE f.realSum IS NOT NULL
),
bench AS (
  -- baseline عادل: متوسط السعر داخل نفس city + room_type
  SELECT city, room_type,
         AVG(realSum) AS city_room_avg,
         COUNT(*) AS n_city_room
  FROM base
  GROUP BY city, room_type
),
scored AS (
  SELECT
    b.*,
    bn.city_room_avg,
    bn.n_city_room,
    (b.realSum - bn.city_room_avg) AS delta_vs_city_room,
    100.0 * (b.realSum - bn.city_room_avg) / NULLIF(bn.city_room_avg, 0) AS delta_pct_vs_city_room,

    -- Feature groups (الجديد هنا)
    CASE
      WHEN b.biz = 1 AND b.multi = 1 THEN 'BIZ+MULTI'
      WHEN b.biz = 1 THEN 'BIZ_ONLY'
      WHEN b.multi = 1 THEN 'MULTI_ONLY'
      ELSE 'STANDARD'
    END AS segment_biz_multi,

    CASE
      WHEN b.room_shared = 1 THEN 'SHARED'
      WHEN b.room_private = 1 THEN 'PRIVATE'
      ELSE 'OTHER'
    END AS privacy_segment,

    CASE
      WHEN amenity_count >= 5 THEN 'AMENITIES_FULL'
      WHEN amenity_count >= 3 THEN 'AMENITIES_COMFORT'
      ELSE 'AMENITIES_BASIC'
    END AS amenity_bundle,

    CASE
      WHEN b.attr_index_norm >= 4 THEN 'HIGH_ATTRACTION'
      WHEN b.attr_index_norm >= 2 THEN 'MID_ATTRACTION'
      ELSE 'LOW_ATTRACTION'
    END AS attraction_band,

    CASE
      WHEN b.rest_index_norm >= 4 THEN 'HIGH_FOOD'
      WHEN b.rest_index_norm >= 2 THEN 'MID_FOOD'
      ELSE 'LOW_FOOD'
    END AS food_band
  FROM base b
  JOIN bench bn ON bn.city=b.city AND bn.room_type=b.room_type
  WHERE bn.n_city_room >= 50
),
impact AS (
  -- نحول كل Feature لتأثير متوسط (Premium/Discount) مقارنة بالbaseline
  SELECT 'segment_biz_multi' AS feature, segment_biz_multi AS feature_value,
         COUNT(*) AS n,
         AVG(delta_pct_vs_city_room) AS avg_premium_pct,
         AVG(delta_vs_city_room) AS avg_premium_amount
  FROM scored
  GROUP BY segment_biz_multi

  UNION ALL
  SELECT 'privacy_segment', privacy_segment,
         COUNT(*), AVG(delta_pct_vs_city_room), AVG(delta_vs_city_room)
  FROM scored
  GROUP BY privacy_segment

  UNION ALL
  SELECT 'amenity_bundle', amenity_bundle,
         COUNT(*), AVG(delta_pct_vs_city_room), AVG(delta_vs_city_room)
  FROM scored
  GROUP BY amenity_bundle

  UNION ALL
  SELECT 'host_is_superhost', CAST(host_is_superhost AS NVARCHAR(10)),
         COUNT(*), AVG(delta_pct_vs_city_room), AVG(delta_vs_city_room)
  FROM scored
  GROUP BY host_is_superhost

  UNION ALL
  SELECT 'weekend', CAST(is_weekend AS NVARCHAR(10)),
         COUNT(*), AVG(delta_pct_vs_city_room), AVG(delta_vs_city_room)
  FROM scored
  GROUP BY is_weekend

  UNION ALL
  SELECT 'attraction_band', attraction_band,
         COUNT(*), AVG(delta_pct_vs_city_room), AVG(delta_vs_city_room)
  FROM scored
  GROUP BY attraction_band

  UNION ALL
  SELECT 'food_band', food_band,
         COUNT(*), AVG(delta_pct_vs_city_room), AVG(delta_vs_city_room)
  FROM scored
  GROUP BY food_band
)
SELECT
  feature,
  feature_value,
  n,
  avg_premium_pct,
  avg_premium_amount,
  DENSE_RANK() OVER (PARTITION BY feature ORDER BY avg_premium_pct DESC) AS feature_rank
FROM impact
WHERE n >= 200
ORDER BY feature, feature_rank;
GO



















--#GeoDemandHotspots
WITH base AS (
  SELECT
    l.country, l.city, l.latitude, l.longitude,
    r.room_type,
    d.is_weekend,
    f.realSum,
    f.metro_dist,
    f.attr_index_norm,
    f.rest_index_norm,
    f.guest_satisfaction_overall
  FROM dbo.Fact_Listings f
  JOIN dbo.Dim_Location  l ON l.location_sk  = f.location_sk
  JOIN dbo.Dim_Room_Type r ON r.room_type_sk = f.room_type_sk
  JOIN dbo.Dim_Day       d ON d.day_sk       = f.day_sk
  WHERE f.realSum IS NOT NULL
    AND l.latitude IS NOT NULL
    AND l.longitude IS NOT NULL
),
grid AS (
  SELECT
    country, city, room_type, is_weekend,
    CAST(ROUND(latitude  / 0.02, 0) AS INT) AS lat_cell,
    CAST(ROUND(longitude / 0.02, 0) AS INT) AS lon_cell,
    realSum, metro_dist, attr_index_norm, rest_index_norm, guest_satisfaction_overall
  FROM base
),
agg AS (
  SELECT
    country, city, room_type,
    lat_cell, lon_cell,
    COUNT(*) AS n,
    AVG(realSum) AS avg_price,
    AVG(attr_index_norm) AS avg_attr,
    AVG(rest_index_norm) AS avg_food,
    AVG(guest_satisfaction_overall) AS avg_sat,
    AVG(CASE WHEN metro_dist <= 0.7 THEN realSum END) AS near_metro_avg,
    AVG(CASE WHEN metro_dist >  0.7 THEN realSum END) AS far_metro_avg,
    AVG(CASE WHEN is_weekend=1 THEN realSum END) AS weekend_avg,
    AVG(CASE WHEN is_weekend=0 THEN realSum END) AS weekday_avg
  FROM grid
  GROUP BY country, city, room_type, lat_cell, lon_cell
  HAVING COUNT(*) >= 80
),
scored AS (
  SELECT
    *,
    (near_metro_avg - far_metro_avg) AS metro_premium_amount,
    100.0 * (near_metro_avg - far_metro_avg) / NULLIF(far_metro_avg,0) AS metro_premium_pct,
    (weekend_avg - weekday_avg) AS weekend_premium_amount,
    100.0 * (weekend_avg - weekday_avg) / NULLIF(weekday_avg,0) AS weekend_premium_pct,

    -- hotspot score جديد: سعر + جذب + أكل + رضا
    (avg_price * 0.45) + (avg_attr * 8.0) + (avg_food * 8.0) + (avg_sat * 0.4) AS hotspot_score
  FROM agg
)
SELECT TOP (150)
  country, city, room_type,
  lat_cell, lon_cell,
  n,
  avg_price, avg_attr, avg_food, avg_sat,
  metro_premium_pct, weekend_premium_pct,
  hotspot_score,
  DENSE_RANK() OVER (PARTITION BY city, room_type ORDER BY hotspot_score DESC) AS hotspot_rank_in_city
FROM scored
ORDER BY hotspot_score DESC;
GO





















WITH base AS (
  SELECT
    l.country, l.city,
    r.room_type,
    h.host_is_superhost,
    d.biz, d.multi, d.is_weekend, d.day_type,
    a.wifi, a.kitchen, a.air_conditioning, a.parking, a.tv, a.heating,
    (CAST(a.wifi AS INT)+CAST(a.kitchen AS INT)+CAST(a.air_conditioning AS INT)+CAST(a.parking AS INT)+CAST(a.tv AS INT)+CAST(a.heating AS INT)) AS amenity_count,
    f.realSum,
    f.attr_index_norm, f.rest_index_norm,
    f.guest_satisfaction_overall
  FROM dbo.Fact_Listings f
  JOIN dbo.Dim_Location  l ON l.location_sk  = f.location_sk
  JOIN dbo.Dim_Room_Type r ON r.room_type_sk = f.room_type_sk
  JOIN dbo.Dim_Host      h ON h.host_sk      = f.host_sk
  JOIN dbo.Dim_Day       d ON d.day_sk       = f.day_sk
  JOIN dbo.Dim_Amenities a ON a.amenity_sk   = f.amenity_sk
  WHERE f.realSum IS NOT NULL
),
seg AS (
  SELECT
    country, city, room_type,
    CASE
      WHEN biz=1 AND multi=1 THEN 'BIZ+MULTI'
      WHEN biz=1 THEN 'BIZ_ONLY'
      WHEN multi=1 THEN 'MULTI_ONLY'
      ELSE 'STANDARD'
    END AS biz_multi_segment,

    CASE
      WHEN amenity_count >= 5 THEN 'AMENITIES_FULL'
      WHEN amenity_count >= 3 THEN 'AMENITIES_COMFORT'
      ELSE 'AMENITIES_BASIC'
    END AS amenity_bundle,

    host_is_superhost,
    is_weekend,

    realSum,
    attr_index_norm, rest_index_norm, guest_satisfaction_overall
  FROM base
),
agg AS (
  SELECT
    country, city, room_type,
    biz_multi_segment,
    amenity_bundle,
    host_is_superhost,

    COUNT(*) AS n,
    AVG(realSum) AS avg_price,
    AVG(attr_index_norm) AS avg_attr,
    AVG(rest_index_norm) AS avg_food,
    AVG(guest_satisfaction_overall) AS avg_sat,

    AVG(CASE WHEN is_weekend=1 THEN realSum END) AS weekend_avg,
    AVG(CASE WHEN is_weekend=0 THEN realSum END) AS weekday_avg
  FROM seg
  GROUP BY country, city, room_type, biz_multi_segment, amenity_bundle, host_is_superhost
  HAVING COUNT(*) >= 80
),
final AS (
  SELECT
    *,
    (weekend_avg - weekday_avg) AS weekend_premium_amount,
    100.0 * (weekend_avg - weekday_avg) / NULLIF(weekday_avg,0) AS weekend_premium_pct,

    -- “strategy score” جديد = جودة + جذب/أكل + استقرار + سعر
    (avg_sat * 0.55) + (avg_attr * 6.0) + (avg_food * 6.0) + (avg_price * 0.08) AS strategy_score,

    CASE
      WHEN weekend_premium_pct >= 10 THEN 'PUSH_WEEKEND_PRICING'
      WHEN weekend_premium_pct <= -5 THEN 'WEEKEND_DISCOUNT_RISK'
      ELSE 'STABLE_WEEKEND'
    END AS weekend_strategy,

    CASE
      WHEN amenity_bundle='AMENITIES_BASIC' AND avg_price > (SELECT AVG(avg_price) FROM agg) THEN 'UPGRADE_AMENITIES_HIGH_ROI'
      WHEN amenity_bundle='AMENITIES_FULL'  AND avg_sat < 88 THEN 'QUALITY_ISSUE_NOT_AMENITIES'
      ELSE 'KEEP_CURRENT_BUNDLE'
    END AS amenity_strategy
  FROM agg
)
SELECT TOP (200)
  country, city, room_type,
  biz_multi_segment,
  amenity_bundle,
  host_is_superhost,
  n,
  avg_price, avg_sat, avg_attr, avg_food,
  weekend_premium_pct,
  strategy_score,
  weekend_strategy,
  amenity_strategy,
  DENSE_RANK() OVER (PARTITION BY country ORDER BY strategy_score DESC) AS country_rank
FROM final
ORDER BY strategy_score DESC;
GO






WITH base AS (
  SELECT
    l.country, l.city,
    r.room_type,
    h.host_is_superhost,
    d.biz, d.multi, d.is_weekend,
    (CAST(a.wifi AS INT)+CAST(a.kitchen AS INT)+CAST(a.air_conditioning AS INT)+CAST(a.parking AS INT)+CAST(a.tv AS INT)+CAST(a.heating AS INT)) AS amenity_count,
    f.realSum,
    f.attr_index_norm, f.rest_index_norm,
    f.guest_satisfaction_overall
  FROM dbo.Fact_Listings f
  JOIN dbo.Dim_Location  l ON l.location_sk  = f.location_sk
  JOIN dbo.Dim_Room_Type r ON r.room_type_sk = f.room_type_sk
  JOIN dbo.Dim_Host      h ON h.host_sk      = f.host_sk
  JOIN dbo.Dim_Day       d ON d.day_sk       = f.day_sk
  JOIN dbo.Dim_Amenities a ON a.amenity_sk   = f.amenity_sk
  WHERE f.realSum IS NOT NULL
),
seg AS (
  SELECT
    country, city, room_type,
    CASE
      WHEN biz=1 AND multi=1 THEN 'BIZ+MULTI'
      WHEN biz=1 THEN 'BIZ_ONLY'
      WHEN multi=1 THEN 'MULTI_ONLY'
      ELSE 'STANDARD'
    END AS biz_multi_segment,
    CASE
      WHEN amenity_count >= 5 THEN 'AMENITIES_FULL'
      WHEN amenity_count >= 3 THEN 'AMENITIES_COMFORT'
      ELSE 'AMENITIES_BASIC'
    END AS amenity_bundle,
    host_is_superhost,
    is_weekend,
    realSum,
    attr_index_norm, rest_index_norm, guest_satisfaction_overall
  FROM base
),
agg AS (
  SELECT
    country, city, room_type, biz_multi_segment, amenity_bundle, host_is_superhost,
    COUNT(*) AS n,
    AVG(realSum) AS avg_price,
    AVG(attr_index_norm) AS avg_attr,
    AVG(rest_index_norm) AS avg_food,
    AVG(guest_satisfaction_overall) AS avg_sat,
    AVG(CASE WHEN is_weekend=1 THEN realSum END) AS weekend_avg,
    AVG(CASE WHEN is_weekend=0 THEN realSum END) AS weekday_avg
  FROM seg
  GROUP BY country, city, room_type, biz_multi_segment, amenity_bundle, host_is_superhost
  HAVING COUNT(*) >= 80
),
final AS (
  SELECT
    *,
    (weekend_avg - weekday_avg) AS weekend_premium_amount,
    100.0 * (weekend_avg - weekday_avg) / NULLIF(weekday_avg,0) AS weekend_premium_pct,
    (avg_sat * 0.55) + (avg_attr * 6.0) + (avg_food * 6.0) + (avg_price * 0.08) AS strategy_score,

    CASE
      WHEN 100.0*(weekend_avg - weekday_avg)/NULLIF(weekday_avg,0) >= 10 THEN 'PUSH_WEEKEND_PRICING'
      WHEN 100.0*(weekend_avg - weekday_avg)/NULLIF(weekday_avg,0) <= -5 THEN 'WEEKEND_DISCOUNT_RISK'
      ELSE 'STABLE_WEEKEND'
    END AS weekend_strategy,

    CASE
      WHEN amenity_bundle='AMENITIES_BASIC' AND avg_price > (SELECT AVG(avg_price) FROM agg)
        THEN 'UPGRADE_AMENITIES_HIGH_ROI'
      WHEN amenity_bundle='AMENITIES_FULL' AND avg_sat < 88
        THEN 'QUALITY_ISSUE_NOT_AMENITIES'
      ELSE 'KEEP_CURRENT_BUNDLE'
    END AS amenity_strategy
  FROM agg
)
SELECT TOP (200)
  country, city, room_type,
  biz_multi_segment,
  amenity_bundle,
  host_is_superhost,
  n,
  avg_price, avg_sat, avg_attr, avg_food,
  weekend_premium_pct,
  strategy_score,
  weekend_strategy,
  amenity_strategy,
  DENSE_RANK() OVER (PARTITION BY country ORDER BY strategy_score DESC) AS country_rank
FROM final
ORDER BY strategy_score DESC;
GO
