from pydantic import BaseModel, ConfigDict


class SchemaModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReadSchemaModel(SchemaModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
