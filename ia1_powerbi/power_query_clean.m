// Requete Power Query optionnelle si tu veux importer directement le clean.csv
// Remplace le chemin si le projet est deplace.

let
    Source = Csv.Document(
        File.Contents("E:\\HEI L2\\Examen\\DONNEE2-SquadAnalytics-1.0.1\\data\\clean\\clean.csv"),
        [Delimiter=",", Columns=9, Encoding=65001, QuoteStyle=QuoteStyle.None]
    ),
    PromotedHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    ChangedTypes = Table.TransformColumnTypes(
        PromotedHeaders,
        {
            {"ville", type text},
            {"latitude", type number},
            {"longitude", type number},
            {"datetime", type datetime},
            {"aqi", Int64.Type},
            {"pm10", type number},
            {"pm2_5", type number},
            {"co", type number},
            {"no2", type number}
        }
    ),
    AddedDate = Table.AddColumn(ChangedTypes, "date", each Date.From([datetime]), type date),
    AddedHour = Table.AddColumn(AddedDate, "heure", each Time.Hour(Time.From([datetime])), Int64.Type),
    AddedWeekend = Table.AddColumn(AddedHour, "weekend", each if Date.DayOfWeek([date], Day.Monday) >= 5 then "Oui" else "Non", type text)
in
    AddedWeekend
