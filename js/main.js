import { AccessParser } from '@regrapes/access-db-parser';

window.parseACCDB = function(arrayBuffer) {
    const db = new AccessParser(Buffer.from(arrayBuffer));
    return db;
};
