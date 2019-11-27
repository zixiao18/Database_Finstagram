SELECT * 
FROM photo JOIN person ON photo.photoPoster = person.username 
WHERE photoPoster IN (SELECT username_followed FROM Follow WHERE username_follower = %s) 
    OR photoPoster = %s 
ORDER BY photoID DESC

-- incorporate friend group

SELECT * 
FROM photo JOIN person ON photo.photoPoster = person.username 
WHERE ((photoPoster IN (SELECT username_followed FROM Follow WHERE username_follower = %s) 
    OR photoPoster = %s) AND allFollowers = 1)
    OR (allFollowers = 0 AND photoPoster IN (SELECT member_username FROM BelongTo WHERE owner_username = %s))
ORDER BY photoID DESC