CREATE TABLE IF NOT EXISTS Contact (
    id SERIAL PRIMARY KEY,
    phoneNumber VARCHAR(255),
    email VARCHAR(255),
    linkedId INTEGER REFERENCES Contact(id),
    linkPrecedence VARCHAR(10) NOT NULL DEFAULT 'primary' CHECK (linkPrecedence IN ('primary', 'secondary')),
    createdAt TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updatedAt TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deletedAt TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_contact_email ON Contact(email);
CREATE INDEX IF NOT EXISTS idx_contact_phone ON Contact(phoneNumber);
